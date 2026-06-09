"""Trace builders for the dashboard time-series charts.

Imported by particle_plus.py::generate_dashboard_html(). Keeping the plot
configuration here (instead of duplicated inline) makes it one small, testable
place to change how the Particle Concentration and PM Concentration series look.

NOTE: this module only builds the base "Raw" step-line traces. The optional
binning (Raw / 10 / 30 / 60 min) and the mean-line + max-dot rendering happen
client-side in features/dashboard/chart_interactions.js, because they must react
to the Bin dropdown without regenerating the page.
"""


def build_series_traces(timestamps, channel_values, names, colors,
                        width=3, shape='hv'):
    """Return one Plotly step-line scatter trace per channel.

    timestamps     : list of x values shared by every channel
    channel_values : list of per-channel y-arrays (same order as names/colors)
    names          : list of trace names
    colors         : list of line colors
    width          : line width (default 3)
    shape          : line interpolation ('hv' = step, holds value until next sample)
    """
    return [
        {
            'x': timestamps, 'y': y, 'name': name,
            'type': 'scatter', 'mode': 'lines',
            'line': {'color': color, 'width': width, 'shape': shape},
        }
        for y, name, color in zip(channel_values, names, colors)
    ]
