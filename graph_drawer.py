import plotly.graph_objects as go
import importlib.util
import logging
import os

from pprint import pprint

from arguments import vprint

class GraphDrawer:

    format_needs_update = []

    def __init__(self, formats=[]):
        self.formats = formats
        if "html" not in formats:
            self.formats.append("html")

        for fmt in formats:
            if fmt not in ["png", "jpeg", "webp", "svg", "pdf"]:
                logging.warning(f"Unknown format {fmt}")
                formats.remove(fmt)

        kaleido = importlib.util.find_spec("kaleido")
        orca = importlib.util.find_spec("orca")

        self.map_writable = kaleido is not None or orca is not None

        if not self.map_writable:
            logging.warning("Install kaleido or orca to save the map as an image")

    def print_graph(self, fig, filename):
        if self.map_writable:
            for fmt in self.format_needs_update:
                vprint(f"Saving {filename}.{fmt}")
                if fmt == "html":
                    fig.write_html(filename + "." + fmt)
                else:
                    fig.write_image(filename + "." + fmt, scale=3, format=fmt)
                vprint(f"Saved {filename}.{fmt}")

        self.format_needs_update = []

    def graph_needs_update(self, filename):
        for fmt in self.formats:
            if not os.path.exists(filename + "." + fmt):
                self.format_needs_update.append(fmt)
        return self.format_needs_update != []

    def ratings_graph(self, data, totals, file_name):

        if not self.graph_needs_update(file_name):
            return
        
        vprint(f"Creating {file_name}...")

        labels = [i for i in range(1, 11)] 
        plot_data = []

        for key in data.keys():
            plot_data.append(go.Bar(name=key, x=labels, y=data[key]))

        fig = go.Figure(data=plot_data)

        total_labels = [{"x": x, "y": total + 15, "text": str(total), "showarrow":False} for x, total in zip(labels, totals)]
        fig.update_layout(barmode='stack',
            xaxis_title="Rating", 
            yaxis_title="Count", 
            xaxis_fixedrange=True,
            yaxis_fixedrange=True,
            xaxis=dict(dtick=1), 
            title_text="Ratings Distribution",
            annotations=total_labels
            )
        
        self.print_graph(fig, file_name)

    def genres_graph(self, data, file_name, media_type):

        if not self.graph_needs_update(file_name):
            return
        
        vprint(f"Creating {file_name}...")

        labels = [genre for genre in data.keys() if media_type in data[genre]]
        sizes = [genre[media_type] for genre in data.values() if media_type in genre]

        fig = go.Figure(data=[go.Pie(labels=labels, values=sizes)])

        fig.update_layout(
            title_text=f'{media_type.capitalize()} Genres'
        )

        self.print_graph(fig, file_name)

    def draw_countries_map(self, data, countries, filename: str, media_type):

        if not self.graph_needs_update(filename):
            return
        
        vprint(f"Creating {filename}...")

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

        self.print_graph(fig, filename)