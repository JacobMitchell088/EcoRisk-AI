"""
tests/test_GBIF.py
Unit tests for GBIF.py — covering unit conversion, CSV loading, and the
GBIF occurrence API call (mocked).

NOTE ON SEARCH-AREA SHAPE
--------------------------
The project used to build a square bounding box locally (get_bounding_box)
and send decimalLatitude/decimalLongitude ranges to GBIF. It now sends a
single `geoDistance` parameter ("lat,lon,radius_meters") and lets GBIF do
the circular search itself. There is no longer a standalone geometry
function to unit-test directly, so the geometry invariants that used to
live in TestSearchAreaContract are now checked by inspecting the params
passed to the mocked `requests.get` call inside
gbif_species_counts_in_area(). See TestGeoDistanceContract below.

If a future implementation goes back to computing geometry locally (e.g.
a polygon search), it's worth reintroducing a small geometry-helper
section here, mirroring what TestBoundingBoxGeometry used to do.
"""

import csv
import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

import GBIF


# ---------------------------------------------------------------------------
# 1. Unit conversion
# ---------------------------------------------------------------------------

class TestMilesToKm:
    def test_known_value(self):
        assert GBIF.miles_to_km(1.0) == pytest.approx(1.609344)

    def test_zero(self):
        assert GBIF.miles_to_km(0.0) == 0.0

    def test_ten_miles(self):
        assert GBIF.miles_to_km(10.0) == pytest.approx(16.09344)

    def test_fractional(self):
        assert GBIF.miles_to_km(0.5) == pytest.approx(0.804672)

    def test_linearity(self):
        """Conversion must be strictly linear: f(2x) == 2*f(x)."""
        assert GBIF.miles_to_km(10.0) == pytest.approx(2 * GBIF.miles_to_km(5.0))


# ---------------------------------------------------------------------------
# 2. CSV loading — load_precomputed_taxon_keys
# ---------------------------------------------------------------------------

def _write_temp_csv(rows: list[dict], fieldnames: list[str]) -> str:
    """Write a CSV to a temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    writer = csv.DictWriter(tmp, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    tmp.close()
    return tmp.name


class TestLoadPrecomputedTaxonKeys:

    def test_normal_load(self):
        path = _write_temp_csv(
            [
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
                {"Scientific Name": "Pandion haliaetus", "Taxon Key": "2480506"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, key_to_name = GBIF.load_precomputed_taxon_keys(path)

        assert name_to_key["Myotis sodalis"] == 2435099
        assert name_to_key["Pandion haliaetus"] == 2480506
        assert key_to_name[2435099] == "Myotis sodalis"
        assert key_to_name[2480506] == "Pandion haliaetus"

    def test_returns_two_dicts(self):
        path = _write_temp_csv(
            [{"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"}],
            ["Scientific Name", "Taxon Key"],
        )
        result = GBIF.load_precomputed_taxon_keys(path)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert isinstance(result[1], dict)

    def test_empty_csv_returns_empty_dicts(self):
        path = _write_temp_csv([], ["Scientific Name", "Taxon Key"])
        name_to_key, key_to_name = GBIF.load_precomputed_taxon_keys(path)
        assert name_to_key == {}
        assert key_to_name == {}

    def test_skips_row_with_empty_name(self):
        path = _write_temp_csv(
            [
                {"Scientific Name": "", "Taxon Key": "2435099"},
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, _ = GBIF.load_precomputed_taxon_keys(path)
        assert len(name_to_key) == 1

    def test_skips_row_with_empty_key(self):
        path = _write_temp_csv(
            [
                {"Scientific Name": "Bad Species", "Taxon Key": ""},
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, _ = GBIF.load_precomputed_taxon_keys(path)
        assert "Bad Species" not in name_to_key
        assert "Myotis sodalis" in name_to_key

    def test_skips_row_with_non_integer_key(self):
        path = _write_temp_csv(
            [
                {"Scientific Name": "Bad Species", "Taxon Key": "not-a-number"},
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, _ = GBIF.load_precomputed_taxon_keys(path)
        assert "Bad Species" not in name_to_key

    def test_strips_whitespace_from_name_and_key(self):
        path = _write_temp_csv(
            [{"Scientific Name": "  Myotis sodalis  ", "Taxon Key": "  2435099  "}],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, key_to_name = GBIF.load_precomputed_taxon_keys(path)
        assert "Myotis sodalis" in name_to_key
        assert 2435099 in key_to_name

    def test_inverse_dicts_are_consistent(self):
        """name_to_key and key_to_name must be exact inverses of each other."""
        path = _write_temp_csv(
            [
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
                {"Scientific Name": "Pandion haliaetus", "Taxon Key": "2480506"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, key_to_name = GBIF.load_precomputed_taxon_keys(path)
        for name, key in name_to_key.items():
            assert key_to_name[key] == name


# ---------------------------------------------------------------------------
# 3. GBIF occurrence API — gbif_species_counts_in_area (mocked)
# ---------------------------------------------------------------------------

class TestGbifSpeciesCountsInArea:

    def _mock_response(self, counts: list[dict]) -> MagicMock:
        mock = MagicMock()
        mock.json.return_value = {"facets": [{"counts": counts}]}
        return mock

    def _params_from_call(self, mock_get):
        call_kwargs = mock_get.call_args
        return call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]

    def test_normal_response_returns_tuples(self, mocker):
        mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([
                {"name": "2435099", "count": "42"},
                {"name": "2480506", "count": "17"},
            ]),
        )
        result = GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        assert result == [(2435099, 42), (2480506, 17)]

    def test_empty_counts_returns_empty_list(self, mocker):
        mocker.patch("GBIF.requests.get", return_value=self._mock_response([]))
        result = GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        assert result == []

    def test_skips_rows_without_name(self, mocker):
        mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([
                {"count": "5"},           # missing "name"
                {"name": "2435099", "count": "10"},
            ]),
        )
        result = GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        assert result == [(2435099, 10)]

    def test_geo_distance_param_sent_to_api(self, mocker):
        """Verify the geoDistance string ('lat,lon,radius_meters') reaches GBIF."""
        mock_get = mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([]),
        )
        lat, lon, radius = 41.8781, -87.6298, 5.0
        GBIF.gbif_species_counts_in_area(lat, lon, radius)
        params = self._params_from_call(mock_get)

        expected_radius_m = GBIF.miles_to_km(radius) * 1000
        assert params["geoDistance"] == f"{lat},{lon},{expected_radius_m}m"

    def test_no_bounding_box_params_present(self, mocker):
        """Old decimalLatitude/decimalLongitude range params must be gone."""
        mock_get = mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([]),
        )
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        params = self._params_from_call(mock_get)
        assert "decimalLatitude" not in params
        assert "decimalLongitude" not in params

    def test_api_called_exactly_once(self, mocker):
        mock_get = mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([]),
        )
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        mock_get.assert_called_once()

    def test_year_filter_in_params(self, mocker):
        mock_get = mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([]),
        )
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        params = self._params_from_call(mock_get)
        assert "year" in params

    # -- Network / HTTP error handling --

    def test_timeout_raises_runtime_error(self, mocker):
        import requests as req
        mocker.patch("GBIF.requests.get", side_effect=req.exceptions.Timeout())
        with pytest.raises(RuntimeError, match="timed out"):
            GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)

    def test_connection_error_raises_runtime_error(self, mocker):
        import requests as req
        mocker.patch("GBIF.requests.get", side_effect=req.exceptions.ConnectionError())
        with pytest.raises(RuntimeError, match="connect"):
            GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)

    def test_http_error_raises_runtime_error(self, mocker):
        import requests as req
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mocker.patch(
            "GBIF.requests.get",
            side_effect=req.exceptions.HTTPError(response=mock_resp),
        )
        with pytest.raises(RuntimeError, match="503"):
            GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)

    def test_generic_request_error_raises_runtime_error(self, mocker):
        import requests as req
        mocker.patch("GBIF.requests.get", side_effect=req.exceptions.RequestException("boom"))
        with pytest.raises(RuntimeError, match="boom"):
            GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)

    def test_empty_facets_returns_empty_list(self, mocker):
        """GBIF sometimes returns no facets when area has no observations."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"facets": []}
        mock_resp.raise_for_status = MagicMock()
        mocker.patch("GBIF.requests.get", return_value=mock_resp)
        result = GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        assert result == []

    def test_missing_facets_key_returns_empty_list(self, mocker):
        """Response missing 'facets' key entirely should not crash."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mocker.patch("GBIF.requests.get", return_value=mock_resp)
        result = GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 5.0)
        assert result == []


# ---------------------------------------------------------------------------
# 4. load_precomputed_taxon_keys() — file error handling
# ---------------------------------------------------------------------------

class TestLoadPrecomputedTaxonKeysErrors:

    def test_missing_file_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="not found"):
            GBIF.load_precomputed_taxon_keys("/nonexistent/path/IllinoisTaxonLookup.csv")

    def test_missing_file_error_message_includes_path(self):
        bad_path = "/nonexistent/path/IllinoisTaxonLookup.csv"
        with pytest.raises(RuntimeError, match=bad_path):
            GBIF.load_precomputed_taxon_keys(bad_path)

    def test_malformed_key_row_is_skipped_and_valid_row_loaded(self):
        """A row with a non-integer key must be skipped; other rows must load."""
        path = _write_temp_csv(
            [
                {"Scientific Name": "Bad Species", "Taxon Key": "not-a-number"},
                {"Scientific Name": "Myotis sodalis", "Taxon Key": "2435099"},
            ],
            ["Scientific Name", "Taxon Key"],
        )
        name_to_key, _ = GBIF.load_precomputed_taxon_keys(path)
        assert "Bad Species" not in name_to_key
        assert "Myotis sodalis" in name_to_key


# ---------------------------------------------------------------------------
# 5. geoDistance contract — shape-agnostic radius invariants
#    These replace the old TestSearchAreaContract. They no longer call a
#    standalone geometry function (get_bounding_box is gone); instead they
#    mock requests.get and inspect the geoDistance string that
#    gbif_species_counts_in_area() actually sends.
# ---------------------------------------------------------------------------
class TestGeoDistanceContract:
    def _mock_response(self) -> MagicMock:
        mock = MagicMock()
        mock.json.return_value = {"facets": [{"counts": []}]}
        return mock

    def _params_from_call(self, mock_get):
        call_kwargs = mock_get.call_args
        return call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]

    def _radius_meters(self, geo_distance: str) -> float:
        """geoDistance is 'lat,lon,<number>m' — strip the unit and parse the number."""
        _, _, radius_str = geo_distance.split(",")
        return float(radius_str.rstrip("m"))

    def test_geo_distance_contains_input_coordinates(self, mocker):
        mock_get = mocker.patch("GBIF.requests.get", return_value=self._mock_response())
        lat, lon = 41.8781, -87.6298
        GBIF.gbif_species_counts_in_area(lat, lon, 5.0)
        params = self._params_from_call(mock_get)
        lat_str, lon_str, _ = params["geoDistance"].split(",")
        assert float(lat_str) == pytest.approx(lat)
        assert float(lon_str) == pytest.approx(lon)

    def test_radius_scales_linearly_with_miles(self, mocker):
        mock_get = mocker.patch("GBIF.requests.get", return_value=self._mock_response())
        lat, lon = 41.8781, -87.6298

        GBIF.gbif_species_counts_in_area(lat, lon, 5.0)
        radius_5 = self._radius_meters(self._params_from_call(mock_get)["geoDistance"])

        mock_get.reset_mock()
        GBIF.gbif_species_counts_in_area(lat, lon, 10.0)
        radius_10 = self._radius_meters(self._params_from_call(mock_get)["geoDistance"])

        assert radius_10 == pytest.approx(2 * radius_5, rel=1e-6)

    def test_larger_radius_gives_larger_geo_distance(self, mocker):
        mock_get = mocker.patch("GBIF.requests.get", return_value=self._mock_response())
        lat, lon = 41.8781, -87.6298

        GBIF.gbif_species_counts_in_area(lat, lon, 5.0)
        radius_5 = self._radius_meters(self._params_from_call(mock_get)["geoDistance"])

        mock_get.reset_mock()
        GBIF.gbif_species_counts_in_area(lat, lon, 20.0)
        radius_20 = self._radius_meters(self._params_from_call(mock_get)["geoDistance"])

        assert radius_20 > radius_5

    def test_zero_radius_gives_zero_distance(self, mocker):
        mock_get = mocker.patch("GBIF.requests.get", return_value=self._mock_response())
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 0.0)
        params = self._params_from_call(mock_get)
        radius = self._radius_meters(params["geoDistance"])
        assert radius == pytest.approx(0.0, abs=1e-9)

    def test_same_inputs_deterministic(self, mocker):
        mock_get = mocker.patch("GBIF.requests.get", return_value=self._mock_response())
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 7.5)
        geo_a = self._params_from_call(mock_get)["geoDistance"]

        mock_get.reset_mock()
        GBIF.gbif_species_counts_in_area(41.8781, -87.6298, 7.5)
        geo_b = self._params_from_call(mock_get)["geoDistance"]

        assert geo_a == geo_b
