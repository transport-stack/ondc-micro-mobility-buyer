from rest_framework import viewsets
import json
import os
import zipfile
from django.http import HttpResponse, JsonResponse
from django.utils.encoding import smart_str
from datetime import datetime

class ONDCBuyerOnStopsSearchViewSet(viewsets.GenericViewSet):
    def search_routes_and_stops(self, request, *args, **kwargs):
        print("on_search.request.data=================", request.body)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON data', status=400)

        data_dir = './data/static_stops_data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        json_file_path = os.path.join(data_dir, 'routes_and_stops.json')
        zip_file_name = f'routes_and_stops.zip'
        zip_file_path = os.path.join(data_dir, zip_file_name)

        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            zipf.write(json_file_path, os.path.basename(json_file_path))

        os.remove(json_file_path)

        zip_file_path_response = {"zip_file_path": zip_file_path}

        with open(zip_file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={smart_str(zip_file_name)}'
            response['Content-Length'] = os.path.getsize(zip_file_path)

        response['Zip-File-Path'] = json.dumps(zip_file_path_response)
        return response
