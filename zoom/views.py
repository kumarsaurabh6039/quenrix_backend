from django.http import JsonResponse
from .services import create_meeting
from .models import ZoomMeeting
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_zoom_meeting(request):
    body = json.loads(request.body)

    topic = body["topic"]
    start_time = body["start_time"]

    zoom_data = create_meeting(topic, start_time)

    meeting = ZoomMeeting.objects.create(
        topic=topic,
        zoom_meeting_id=zoom_data["id"],
        start_url=zoom_data["start_url"],
        join_url=zoom_data["join_url"],
        start_time=start_time
    )

    return JsonResponse({
        "id": meeting.id,
        "join_url": meeting.join_url
    })



from .services import get_recordings

@csrf_exempt
def list_recordings(request):
    data = get_recordings()
    return JsonResponse(data)
