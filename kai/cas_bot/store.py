
class BaseStore:

    def user_exists(self, user_id):
        ...

    def add_user(self, user_id):
        ...

    def remove_user(self, user_id):
        ...

    def get_all_users(self):
        ...


class MemStore(BaseStore):
    user_store: dict

    def __init__(self):
        self.user_store = {}

    def user_exists(self, user_id):
        return user_id in self.user_store
    def add_user(self, user_id):
        self.user_store[user_id]=user_id

    def remove_user(self, user_id):
        del self.user_store[user_id]

    def get_all_users(self):
        return list(self.user_store.values())
