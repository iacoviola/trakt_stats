import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import importlib.util

from pprint import pprint

class GraphDrawer:

    def draw_bar_graph(self, x, y, title, xlabel, ylabel, file_name: str):

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

    def draw_countries_map(self, data, countries, filename: str, media_type, format=None):

        # [0.5, 'rgb(156, 156, 255)'] add at second position
        colorscales = [[0, 'rgb(0, 0, 128)'], [0.95, 'rgb(128, 128, 200)'], [1, 'rgb(255, 255, 255)']]      
        country_values = [data[country][media_type] if country in data.keys() and media_type in data[country].keys() else 0 for country in countries]

        fig = go.Figure(data=go.Choropleth(
            locations=[countries[country]["alpha-3"] for country in countries],
            z=country_values,
            text=[countries[country]["name"] for country in countries],
            colorscale=colorscales,
            autocolorscale=False,
            reversescale=True,
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_tickprefix='',
            colorbar_title=media_type.capitalize()
        ))

        fig.update_layout(
            title_text=f'{media_type.capitalize()} by Country',
            #paper_bgcolor='black',
            geo=dict(
                #bgcolor='black',
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular'
            ),
            #font=dict(color='white'),
            yaxis_showgrid=False,
            xaxis_showgrid=False
        )

        fig.update_geos(
            showlakes=False,
            showland=False,
            showcountries=True
        )

        fig.write_html(filename + ".html")

        kaleido = importlib.util.find_spec("kaleido")
        orca = importlib.util.find_spec("orca")

        if kaleido is not None or orca is not None:
            if format is not None:
                for fmt in format:
                    fig.write_image(filename + "." + fmt, scale=3, format=fmt)
        else:
            print("Install kaleido or orca to save as svg, png, jpeg, webp and pdf")