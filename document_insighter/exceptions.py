class ChannelLogExistsError(Exception):

    def __init__(self, md5_hash, existing_channel_ids):
        self.md5_hash = md5_hash
        self.existing_channel_ids = existing_channel_ids
        super().__init__(f"Channel log with md5 hash {md5_hash} already exists for channel ids {existing_channel_ids}")