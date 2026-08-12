from cloudinary import CloudinaryResource
from cloudinary_storage.storage import VideoMediaCloudinaryStorage

# Cloudinary delivery transformation applied to every served video URL.
# Re-encodes to MP4 (H.264), caps width at Full HD, and uses near-lossless
# auto quality so hero / highlight reels keep their cinematic sharpness.
VIDEO_TRANSFORMATIONS = [
    {"width": 1920, "crop": "limit", "quality": "auto:best", "fetch_format": "mp4"}
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
