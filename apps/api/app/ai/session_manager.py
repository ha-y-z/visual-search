import uuid


class SessionManager:
    def __init__(self):
        self.current_session_id = str(uuid.uuid4())

    def get_current_session_id(self):
        return self.current_session_id

    def replace_new_session_id(self):
        self.current_session_id = str(uuid.uuid4())
        return self.current_session_id
