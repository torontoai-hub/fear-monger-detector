"""charts.py - Create charts with hover tooltips and download support"""
import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go


def create_matplotlib_chart(seconds, scores, talk_index, chart_type="Line Chart"):
    """Create matplotlib chart based on selected type"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if chart_type == "Line Chart":
        ax.plot(seconds, scores, color='blue', marker='o', linestyle='-', linewidth=2, markersize=4)
    elif chart_type == "Bar Chart":
        ax.bar(seconds, scores, color='blue', width=(seconds[1] - seconds[0]) * 0.8 if len(seconds) > 1 else 1)
    elif chart_type == "Area Chart":
        ax.fill_between(seconds, scores, color='blue', alpha=0.3)
        ax.plot(seconds, scores, color='blue', linewidth=2)
    
    ax.set_xlabel('Elapsed Time (HH:MM:SS)')
    ax.set_ylabel('Fear Mongering Score')
    ax.set_title(f'Fear Mongering Score vs Time for Talk Index {talk_index} ({chart_type})')
    ax.grid(True)
    ax.set_ylim(0, 1)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def create_plotly_chart(seconds, scores, paragraphs, talk_index, chart_type="Line Chart", max_hover_length=100):
    """Create interactive Plotly chart with hover tooltips based on selected type."""
    
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    time_axis = [start_time + datetime.timedelta(seconds=s) for s in seconds]

    hover_texts = [
        f"Paragraph: {p[:max_hover_length]}{'...' if len(p) > max_hover_length else ''}<br>"
        f"Score: {score:.2f}"
        for p, score in zip(paragraphs, scores)
    ]

    fig = go.Figure()
    
    if chart_type == "Line Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            # mode='lines+markers',
            mode='lines',
            line=dict(color='blue', width=2),
            marker=dict(size=8),  # Larger markers for easier hovering
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Bar Chart":
        fig.add_trace(go.Bar(
            x=time_axis,
            y=scores,
            marker=dict(color='blue'),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Area Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            mode='lines',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.3)',
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))

    fig.update_xaxes(
        tickformat="%H:%M:%S",
        title_text="Elapsed Time (HH:MM:SS)",
        showgrid=True,
        gridcolor="#333"
    )
    
    fig.update_yaxes(
        title_text="Score",
        range=[0, 1],
        showgrid=True,
        gridcolor="#333"
    )

    fig.update_layout(
        
        title=f"Fear Mongering Score vs Time for Talk Index {talk_index} ({chart_type})",
        xaxis=dict(
            title=f"Fear Mongering Score vs Time for Talk Index {talk_index} ({chart_type})",
            paper_bgcolor="#0e1117",    # Dark background
            plot_bgcolor="#0e1117",     # Dark plotting area
            font=dict(color="#fafafa"), # Light font color
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1m', step='minute', stepmode='backward'),
                    dict(count=5, label='5m', step='minute', stepmode='backward'),
                    dict(count=15, label='15m', step='minute', stepmode='backward'),
                    dict(step='all')
                ]
            ),
            rangeslider=dict(visible=False),
            type='date'
        ),
        # hovermode='closest',  # Use 'closest' for pointer on data points
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            align='left',  # Global alignment
            bordercolor='blue'
        ),
        dragmode='pan', # This changes the default cursor behavior
        legend=dict(bgcolor="#262730") 
    )

    return fig