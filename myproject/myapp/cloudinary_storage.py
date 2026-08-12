from cloudinary import CloudinaryResource
from cloudinary_storage.storage import VideoMediaCloudinaryStorage

# Videos are delivered in their ORIGINAL quality — no re-encode, no downscale.
# Upload an H.264 MP4 (AAC audio) for the widest browser support, especially
# Safari/iOS, which cannot play WebM or non-H.264 codecs.
VIDEO_TRANSFORMATIONS = []


class SmartVideoCloudinaryStorage(VideoMediaCloudinaryStorage):
    def _get_url(self, name):
        name = self._prepend_prefix(name)
        resource = CloudinaryResource(
            name,
            default_resource_type=self._get_resource_type(name),
            url_options={"transformation": VIDEO_TRANSFORMATIONS},
        )
        return resource.url
