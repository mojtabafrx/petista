import jdatetime


def current_jalali_year(request):
    jalali_year = jdatetime.datetime.now().year
    return {'current_jalali_year': jalali_year}
