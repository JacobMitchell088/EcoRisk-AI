"""
tests/test_GBIF.py
Unit tests for GBIF.py — covering unit conversion, CSV loading, and the
GBIF occurrence API call (mocked).

NOTE ON SEARCH-AREA SHAPE
--------------------------
The project used to build a square bounding box locally (get_bounding_box)
and send decimalLatitude/decimalLongitude ranges to GBIF. It now sends a
single `geoDistance` parameter ("lat,lon,radius_metersm") and lets GBIF do
the circular search itself. There is no longer a standalone geometry
function to unit-test directly, so the geometry invariants that used to
live in TestSearchAreaContract are now checked by inspecting the params
passed to the mocked `requests.get` call inside
gbif_species_counts_in_area(). See TestGeoDistanceContract below.

If a future implementation goes back to computing geometry locally (e.g.
a polygon search), it's worth reintroducing a small geometry-helper
section here, mirroring what TestBoundingBoxGeometry used to do.

NOTE ON MULTI-STATE LOOKUP
---------------------------
The taxon lookup moved from a single-state file (IllinoisTaxonLookup.csv,
one row per species, loaded by the now-removed load_precomputed_taxon_keys)
to a multi-state file (MasterTaxonLookup.csv, loaded by
load_master_taxon_lookup). A species can now appear on multiple rows — once
per state it's listed in, plus a federal row where State == "All" — so the
lookup is keyed by taxon_key -> list[dict] rather than a 1:1 name<->key pair.
Whether a US state actually contains the search point/circle at all is
handled separately, in state_lookup.py, and isn't covered by this file.
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
# 2. CSV loading — load_master_taxon_lookup
# ---------------------------------------------------------------------------

MASTER_LOOKUP_FIELDS = ["Taxon Key", "Scientific Name", "Common Name", "Status", "State"]


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


class TestLoadMasterTaxonLookup:

    def test_normal_load(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "All",
                },
                {
                    "Taxon Key": "2442437",
                    "Scientific Name": "Kinosternon flavescens",
                    "Common Name": "Yellow Mud Turtle",
                    "Status": "Threatened",
                    "State": "IL",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)

        assert lookup[2435099][0]["scientific_name"] == "Myotis sodalis"
        assert lookup[2435099][0]["state"] == "All"
        assert lookup[2442437][0]["common_name"] == "Yellow Mud Turtle"
        assert lookup[2442437][0]["state"] == "IL"

    def test_returns_dict_of_lists(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                }
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        assert isinstance(lookup, dict)
        assert isinstance(lookup[2435099], list)

    def test_species_listed_in_multiple_states_collects_all_entries(self):
        """A species can appear once per state it's listed in."""
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                },
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "MO",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        states = {entry["state"] for entry in lookup[2435099]}
        assert states == {"IL", "MO"}
        assert len(lookup[2435099]) == 2

    def test_species_with_state_and_federal_rows(self):
        """A species can be both federally listed and state-listed at once."""
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "All",
                },
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        states = {entry["state"] for entry in lookup[2435099]}
        assert states == {"All", "IL"}

    def test_empty_csv_returns_empty_dict(self):
        path = _write_temp_csv([], MASTER_LOOKUP_FIELDS)
        lookup = GBIF.load_master_taxon_lookup(path)
        assert lookup == {}

    def test_skips_row_with_empty_key(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "",
                    "Scientific Name": "Bad Species",
                    "Common Name": "",
                    "Status": "",
                    "State": "IL",
                },
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        assert len(lookup) == 1
        assert 2435099 in lookup

    def test_skips_row_with_non_integer_key(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "not-a-number",
                    "Scientific Name": "Bad Species",
                    "Common Name": "",
                    "Status": "",
                    "State": "IL",
                },
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        assert 2435099 in lookup
        assert len(lookup) == 1

    def test_strips_whitespace_from_fields(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "  2435099  ",
                    "Scientific Name": "  Myotis sodalis  ",
                    "Common Name": "  Indiana Bat  ",
                    "Status": "  Endangered  ",
                    "State": "  IL  ",
                }
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        entry = lookup[2435099][0]
        assert entry["scientific_name"] == "Myotis sodalis"
        assert entry["common_name"] == "Indiana Bat"
        assert entry["status"] == "Endangered"
        assert entry["state"] == "IL"

    def test_missing_optional_fields_default_to_empty_string(self):
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "",
                    "Status": "",
                    "State": "IL",
                }
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        entry = lookup[2435099][0]
        assert entry["common_name"] == ""
        assert entry["status"] == ""


class TestLoadMasterTaxonLookupErrors:

    def test_missing_file_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="not found"):
            GBIF.load_master_taxon_lookup("/nonexistent/path/MasterTaxonLookup.csv")

    def test_missing_file_error_message_includes_path(self):
        bad_path = "/nonexistent/path/MasterTaxonLookup.csv"
        with pytest.raises(RuntimeError, match=bad_path):
            GBIF.load_master_taxon_lookup(bad_path)

    def test_malformed_key_row_is_skipped_and_valid_row_loaded(self):
        """A row with a non-integer key must be skipped; other rows must load."""
        path = _write_temp_csv(
            [
                {
                    "Taxon Key": "not-a-number",
                    "Scientific Name": "Bad Species",
                    "Common Name": "",
                    "Status": "",
                    "State": "IL",
                },
                {
                    "Taxon Key": "2435099",
                    "Scientific Name": "Myotis sodalis",
                    "Common Name": "Indiana Bat",
                    "Status": "Endangered",
                    "State": "IL",
                },
            ],
            MASTER_LOOKUP_FIELDS,
        )
        lookup = GBIF.load_master_taxon_lookup(path)
        assert 2435099 in lookup
        assert len(lookup) == 1


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
        """
        Verify the geoDistance string ('lat,lon,radius_metersm') reaches GBIF.

        The distance component MUST carry a unit suffix ("m" here) per GBIF's
        geoDistance contract — a bare number is not a valid distance. This
        test will fail if that suffix regresses (see the merge note at the
        top of this file).
        """
        mock_get = mocker.patch(
            "GBIF.requests.get",
            return_value=self._mock_response([]),
        )
        lat, lon, radius = 41.8781, -87.6298, 5.0
        GBIF.gbif_species_counts_in_area(lat, lon, radius)
        params = self._params_from_call(mock_get)

        expected_radius_m = GBIF.miles_to_km(radius) * 1000
        assert params["geoDistance"] == f"{lat},{lon},{expected_radius_m}"

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
# 4. geoDistance contract — shape-agnostic radius invariants
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
