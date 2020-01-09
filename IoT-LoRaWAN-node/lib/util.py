def get_date_str(date_tuple):
    return (
        str(date_tuple[0])
        + '-' + ('0' if date_tuple[1] < 10 else '') + str(date_tuple[1])
        + '-' + ('0' if date_tuple[2] < 10 else '') + str(date_tuple[2])

        + '_' + ('0' if date_tuple[3] < 10 else '') + str(date_tuple[3])
        + '-' + ('0' if date_tuple[4] < 10 else '') + str(date_tuple[4])
        + '-' + ('0' if date_tuple[5] < 10 else '') + str(date_tuple[5])

        + '.' + str(date_tuple[6])
    )


#changes from Degrees and decimal minutes (DMM) to Decimal degrees (DM)
# https://www.ubergizmo.com/how-to/read-gps-coordinates/
def coord_deg_to_dec(coord_tuple):
    return (coord_tuple[0] + (coord_tuple[1] / 60)) * (1 if coord_tuple[2] == "N" or coord_tuple[2] == "E" else -1)
