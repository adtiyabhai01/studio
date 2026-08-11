from cloudinary import CloudinaryResource
from cloudinary_storage.storage import VideoMediaCloudinaryStorage

# Cloudinary delivery transformation applied to every served video URL.
# Re-encodes to MP4 (H.264) with auto quality and caps width at Full HD,
# so large uploads are streamed to browsers in a much smaller size.
VIDEO_TRANSFORMATIONS = [
    {"width": 1920, "crop": "limit", "quality": "auto", "fetch_format": "mp4"}
]


class SmartVideoCloudinaryStorage(VideoMediaCloudinaryStorage):
    def _get_url(self, name):
        name = self._prepend_prefix(name)
        resource = CloudinaryResource(
            name,
            default_resource_type=self._get_resource_type(name),
            url_options={"transformation": VIDEO_TRANSFORMATIONS},
        )
        return resource.url
