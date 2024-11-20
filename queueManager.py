# class QueueManager:
#     def __init__(self):
#         self.queue = []
#         self.current_index = -1

#     def add_songs(self, songs):
#         self.queue.extend(songs)
#         if self.current_index == -1:
#             self.current_index = 0

#     def clear_queue(self):
#         self.queue = []
#         self.current_index = -1

#     def get_current_song(self):
#         if 0 <= self.current_index < len(self.queue):
#             return self.queue[self.current_index]
#         return None

#     def get_next_song(self):
#         if self.current_index + 1 < len(self.queue):
#             self.current_index += 1
#             return self.queue[self.current_index]
#         return None

#     def has_next_song(self):
#         return self.current_index + 1 < len(self.queue)

# class QueueManager:
#     def __init__(self):
#         self.queue = []
#         self.current_index = -1
#         self.loop_mode = 'no_loop'  # Possible values: 'no_loop', 'loop_one', 'loop_all'

#     def add_songs(self, songs):
#         self.queue.extend(songs)
#         if self.current_index == -1:
#             self.current_index = 0

#     def clear_queue(self):
#         self.queue = []
#         self.current_index = -1

#     def get_current_song(self):
#         if 0 <= self.current_index < len(self.queue):
#             return self.queue[self.current_index]
#         return None

#     def get_next_song(self):
#         if self.loop_mode == 'loop_one':
#             return self.queue[self.current_index]
#         elif self.loop_mode == 'loop_all' and self.current_index + 1 >= len(self.queue):
#             self.current_index = 0
#             return self.queue[0]
#         elif self.current_index + 1 < len(self.queue):
#             self.current_index += 1
#             return self.queue[self.current_index]
#         return None

#     def has_next_song(self):
#         return (self.loop_mode in ['loop_one', 'loop_all'] or 
#                 self.current_index + 1 < len(self.queue))


class QueueManager:
    def __init__(self):
        self.queue = []
        self.current_index = -1
        self.loop_mode = 'no_loop'  # Possible values: 'no_loop', 'loop_one', 'loop_all'

    def add_songs(self, songs):
        self.queue.extend(songs)
        if self.current_index == -1:
            self.current_index = 0

    def clear_queue(self):
        self.queue = []
        self.current_index = -1

    def get_current_song(self):
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    def get_next_song(self):
        if self.loop_mode == 'loop_one':
            return self.queue[self.current_index]
        elif self.loop_mode == 'loop_all' and self.current_index + 1 >= len(self.queue):
            self.current_index = 0
            return self.queue[0]
        elif self.current_index + 1 < len(self.queue):
            self.current_index += 1
            return self.queue[self.current_index]
        return None

    def has_next_song(self):
        return (self.loop_mode in ['loop_one', 'loop_all'] or 
                self.current_index + 1 < len(self.queue))
    
    def get_all_songs(self):
        """
        Returns all songs in the queue along with their indices and current playing status.
        Returns a list of dictionaries containing song information.
        """
        all_songs = []
        for index, song in enumerate(self.queue):
            song_info = {
                'index': index,
                'song': song,
                'is_current': index == self.current_index
            }
            all_songs.append(song_info)
        return all_songs