def extract_hole_or_tee_time(competitor):
    tee_time_keys = ["teeTime", "teeTimeDisplay", "startTime", "displayTime"]

    for key in tee_time_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return format_tee_time(value)

    # Check status first — if the golfer is finished, return "F"
    state_val = get_status_state(competitor)
    if state_val == "post":
        return "F"

    play_status_keys = ["thru", "thruStatus", "currentHole", "currentHoleNumber", "hole"]

    for key in play_status_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return display_hole_value(value)

    status = competitor.get("status")
    if isinstance(status, dict):
        for key in ["displayValue", "detail", "shortDetail", "description"]:
            value = clean_status_text(status.get(key))
            if value:
                return display_hole_value(value)

        status_type = status.get("type")
        if isinstance(status_type, dict):
            for key in ["detail", "shortDetail", "description", "name"]:
                value = clean_status_text(status_type.get(key))
                if value:
                    return display_hole_value(value)

    linescores = competitor.get("linescores")
    if isinstance(linescores, list) and linescores:
        latest = linescores[-1]
        if isinstance(latest, dict):
            for key in ["thru", "thruStatus", "currentHole", "displayValue", "value"]:
                value = clean_status_text(latest.get(key))
                if value and value not in ["--"]:
                    return display_hole_value(value)

    return "—"
