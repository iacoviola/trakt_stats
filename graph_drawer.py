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

    def draw_genres_graph(self, data, file_name):
        genres = list(data.keys())
        movie_counts = [genre["movies"] for genre in data.values()]
        show_counts = [genre["shows"] for genre in data.values()]

        fig, ax = plt.subplots(figsize=(14, 1))
        width_sum = 0
        for i in range(len(genres)):
            curr_width = movie_counts[i] if movie_counts[i] > 200 else 200
            ax.barh("Movies", curr_width, .1, left=width_sum, edgecolor='white')
            ax.text(width_sum + curr_width / 2, 0, movie_counts[i], ha='center', va='center', color='white')
            width_sum += curr_width

        ax.set_title("Genres")
        ax.set_xticks([])
        ax.set_xlabel("Number of movies and shows")
        ax.set_yticks([])
        ax.set_ylabel("Genres")
        ax.grid(False)

        plt.savefig(file_name, bbox_inches='tight', dpi=300)
        #plt.close()