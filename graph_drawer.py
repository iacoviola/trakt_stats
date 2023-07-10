import matplotlib.pyplot as plt
import numpy as np

from pprint import pprint

class GraphDrawer:

    def draw_bar_graph(self, x, y, title, xlabel, ylabel, file_name):

        fig, ax = plt.subplots()
        
        ax.bar(np.arange(1, x + 1), y)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xticks(np.arange(1, x + 1))
        ax.grid(False)

        for x in ax.patches:
            ax.annotate(str(x.get_height()), (x.get_x() + x.get_width() / 2, x.get_height()), ha='center', va='bottom')

        #save as png
        plt.savefig(file_name, bbox_inches='tight', dpi=300)
        #plt.show()

    def draw_pie_graph(self, data):

        fig, ax = plt.subplots()

        ax.pie(data.values(), labels=data.keys(), startangle=90)

        plt.savefig("genres.png", bbox_inches='tight', dpi=300)
        plt.show()

    def draw_genres_graph(self, data, file_name, media_type):
        media_genres = [genre for genre in data.keys() if media_type in genre]
        media_counts = [genre[media_type] for genre in data.values() if media_type in genre]

        fig, ax = plt.subplots(figsize=(14, 1))
        width_sum = 0
        for i in range(len(media_counts)):
            curr_width = media_counts[i] if media_counts[i] > 200 else 200
            ax.barh("Movies", curr_width, .1, left=width_sum, edgecolor='white')
            ax.text(width_sum + curr_width / 2, 0, media_counts[i], ha='center', va='center', color='white')
            width_sum += curr_width

        ax.set_title("Genres")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)

        plt.savefig(file_name, bbox_inches='tight', dpi=300)
        #plt.close()