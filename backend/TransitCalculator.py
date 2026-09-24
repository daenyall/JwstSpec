
class TransitCalculator:
    def calculate_transit_window(self, t0, p, duration_hours, tobs):
        formatted_t0 = t0 - 2400000.5
        n = round((tobs - formatted_t0) / p)
        mid_transit = formatted_t0 + n * p
        duration_days = duration_hours / 24
        half_duration = duration_days / 2

        transit_start = mid_transit - half_duration
        transit_end = mid_transit + half_duration

        return mid_transit, transit_start, transit_end,  duration_hours

        
        
