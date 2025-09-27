import csv
from io import StringIO
from django.http import HttpResponse


def export_to_csv(filename: str, header: list, rows: list):
    """
    Gera um CSV com base no cabeçalho e linhas passadas.
    Compatível com Excel (UTF-8 BOM).
    """
    import csv
    from io import StringIO
    from django.http import HttpResponse

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)

    response = HttpResponse(
        '\ufeff' + buffer.getvalue(),
        content_type="text/csv"
    )
    response["Content-Disposition"] = f'attachment; filename=\"{filename}.csv\"'
    return response
