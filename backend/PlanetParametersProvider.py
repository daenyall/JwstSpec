import math
import requests


class PlanetParametersProvider:
    def __init__(self):
        self.base_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

    def get_parameters(self, target, tobs):
        archive_target = self._format_planet_name(target)
        safe_target = archive_target.replace("'", "''")

        query = (
            "select pl_name,pl_tranmid,pl_tranmiderr1,pl_tranmiderr2,"
            "pl_orbper,pl_orbpererr1,pl_orbpererr2,"
            "pl_trandur,pl_tsystemref,pl_refname "
            f"from ps where pl_name='{safe_target}'"
        )

        rows = self._request(query)

        if not rows:
            raise ValueError(f"Planet not found in NASA Exoplanet Archive: {target}")

        candidates = []

        for row in rows:
            if row["pl_tranmid"] is None:
                continue

            if row["pl_orbper"] is None:
                continue

            if row["pl_tsystemref"] is None:
                continue

            time_system = self._normalize_time_system(row["pl_tsystemref"])

            if time_system != "BJD-TDB":
                continue

            candidates.append(row)

        if not candidates:
            raise ValueError(f"No BJD-TDB ephemeris found for {target}")

        tobs_jd = tobs + 2400000.5

        best_row = min(
            candidates,
            key=lambda row: self._calculate_ephemeris_score(row, tobs_jd)
        )

        if best_row["pl_trandur"] is not None:
            duration_hours = float(best_row["pl_trandur"])
            duration_source = "PS"
        else:
            duration_hours = self._get_composite_duration(safe_target)
            duration_source = "PSCompPars fallback"

        return {
            "planet_name": best_row["pl_name"],
            "t0": float(best_row["pl_tranmid"]),
            "period_days": float(best_row["pl_orbper"]),
            "duration_hours": duration_hours,
            "time_system": best_row["pl_tsystemref"],
            "reference": best_row["pl_refname"],
            "duration_source": duration_source
        }

    def _get_composite_duration(self, safe_target):
        query = f"select pl_trandur from pscomppars where pl_name='{safe_target}'"

        rows = self._request(query)

        if not rows:
            raise ValueError("No PSCompPars entry found for transit duration")

        duration = rows[0]["pl_trandur"]

        if duration is None:
            raise ValueError("No transit duration available in PSCompPars")

        return float(duration)

    def _calculate_ephemeris_score(self, row, tobs_jd):
        t0 = float(row["pl_tranmid"])
        period = float(row["pl_orbper"])

        n = round((tobs_jd - t0) / period)

        t0_error = self._largest_error(row["pl_tranmiderr1"], row["pl_tranmiderr2"])
        period_error = self._largest_error(row["pl_orbpererr1"], row["pl_orbpererr2"])

        if t0_error is None or period_error is None:
            return float("inf")

        predicted_error = math.sqrt(t0_error ** 2 + (n * period_error) ** 2)

        return predicted_error

    def _largest_error(self, error1, error2):
        errors = []

        if error1 is not None:
            errors.append(abs(float(error1)))

        if error2 is not None:
            errors.append(abs(float(error2)))

        if not errors:
            return None

        return max(errors)

    def _request(self, query):
        response = requests.get(
            self.base_url,
            params={
                "query": query,
                "format": "json"
            },
            timeout=30
        )

        if not response.ok:
            raise RuntimeError(
                f"NASA Exoplanet Archive error {response.status_code}: {response.text}"
            )

        return response.json()

    def _normalize_time_system(self, time_system):
        return time_system.upper().replace("_", "-").replace(" ", "")

    def _format_planet_name(self, target):
        target = target.strip()

        if len(target) >= 2 and target[-1].isalpha() and target[-2] != " ":
            return target[:-1] + " " + target[-1]

        return target