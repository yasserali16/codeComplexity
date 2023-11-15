import numpy as np
import pandas as pd
import datetime
#import locale # werkt niet binnen Azure



DF_PRINT_LENGTH = 10
def format_int_func(num: int) -> str:
    return '{:,}'.format(int(num)).replace(',', '.')

def format_number_func(num: float) -> str:
    return '{:,.2f}'.format(num).replace(',', 'COMMA').replace('.', ',').replace('COMMA', '.')

def format_big_number(num:int, indx):
    """ used in y axis of graphs """
    if num >= 1_000_000_000 or num <= -1_000_000_000:
        frmted = '{:1.1f} B'.format(num*0.000_000_001)
    elif num >= 1_000_000 or num <= -1_000_000:
        frmted = '{:1.1f} M'.format(num*0.000_001)
    else:
        frmted = '{:1.1f} K'.format(num*0.001)
    return frmted
    
def generate_table_frame(df: pd.DataFrame) -> str:
    """Function to generate html table for the homepage given pandas dataframe"""
    return_df = df.to_html(escape=False, classes=['table', 'table-striped', 'table-light', 'style-3']).replace('border="1"','').replace('style="text-align: right;"', '')
    return return_df

def prepare_html_frame(df: pd.DataFrame) -> str:
    """Function to generate html table for the chat response given pandas dataframe"""
    return_df = df.to_html(escape=False, index=False, classes=['table', 'table-striped', 'table-light', 'overflow-auto', 'd-inline-block', 'style-3']).replace('border="1"','').replace('style="text-align: right;"', '')
    return return_df 

def generate_html_reponse(df: pd.DataFrame, response_id: int, extra_text: str = '') -> str:
    """Function to add download button and extra text for chatbot response"""
    response = df
    if len(extra_text) > 0:
        response += '<div>{}</div>'.format(extra_text)
    return response + '<div><i class="bi bi-file-earmark-arrow-down-fill export_from_response" role="button" id="{}" title="Download Excel"></i></div>'.format(response_id)

def return_response_df(ans: pd.DataFrame, response_id: int) -> str:
    """Function to limit df size to 10 for response purpose and define extra text if to big"""
    extra_text = ''
    if len(ans) == 0:
        return 'Er is niks gevonden'
    new_ans = prepare_html_frame(ans.head(DF_PRINT_LENGTH))
    if len(ans) > DF_PRINT_LENGTH:
        extra_text = 'Download via de button hieronder het volledige antwoord'
    return generate_html_reponse(new_ans, response_id, extra_text)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import io
import base64

def plot_to_base64(fig, title=None):
    """Convert a matplotlib figure to base64-encoded image"""
    if title:
        fig.suptitle(title, fontsize=12)  # Set the title for the figure
    
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)
    
    encoded_img = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)  # Close the figure to release resources
    return encoded_img


import time
import random

# Define a dictionary to store the unique identifiers for plots
plot_identifiers = {}

from matplotlib.ticker import MaxNLocator

dutch_month_names = {
    1: 'januari',
    2: 'februari',
    3: 'maart',
    4: 'april',
    5: 'mei',
    6: 'juni',
    7: 'juli',
    8: 'augustus',
    9: 'september',
    10: 'oktober',
    11: 'november',
    12: 'december'
}
# Define a list of months in Dutch in the correct order
months_in_dutch = [
    "januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"
]

def style_answer(ans, response_id, plot_title=None):
    """Function to delegate answer to proper type and process function"""
    html_list = []  # List to store HTML content

    if isinstance(ans, (np.integer, int)):
        return format_int_func(int(ans))
    elif type(ans) == str:
        return ans
    elif isinstance(ans, (np.floating, float)):
        return format_number_func(float(ans))
    elif isinstance(ans, (np.bool_, bool)):
        return 'Ja' if ans else 'Nee'
    elif isinstance(ans, pd.Timestamp):
        d = ans.strftime('%d')
        m = dutch_month_names[int(ans.strftime('%m'))]
        y = ans.strftime('%Y')
        frmted = f"{d} {m} {y}"
        return frmted # ans.strftime('%d %B %Y') 
    elif isinstance(ans, np.ndarray):
        if len(ans) > 5:
            ans = pd.DataFrame(ans, columns=['Lijst'])
            return return_response_df(ans, response_id)
        else:
            return str(ans)  # hardcoded naar lengte 5
    elif hasattr(ans, 'get_figure') and callable(getattr(ans, 'get_figure')):
        fig = ans.get_figure()
        plt.close(fig)  # Close the figure to release resources

        # Generate a unique identifier for the plot
        unique_id = f"{response_id}_{int(time.time())}_{random.randint(1, 1000)}"
        plot_identifiers[unique_id] = fig

        # Customize the plot
        fig.suptitle(plot_title, fontsize=16)
        ax = fig.gca()

        # Automatically determine the maximum number of tick locations based on available space
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        if ans.get_xlabel() == "Maand":
            xlabels = months_in_dutch  # Set x-axis labels to months in Dutch
            ax.set_xticks(range(len(xlabels)))  # Set tick positions for all months
            ax.set_xticklabels(xlabels, rotation=45, ha='right')
            
        ax.yaxis.set_major_formatter(format_big_number)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        ax.tick_params(axis='both', which='major', labelsize=10)
        fig.tight_layout()

        # Convert the plot to base64
        encoded_img = plot_to_base64(fig)
        plt.close(fig)  # Close the figure to release resources

        # Generate HTML to display the image with the unique identifier and a download link
        html = f'<div style="text-align: center;">'
        html += f'<img id="plot-image-{unique_id}" src="data:image/png;base64,{encoded_img}" alt="Plot">'
        html += f'<button><a href="data:image/png;base64,{encoded_img}" download="plot.png">Download Grafiek</a></button>'
        html += '</div>'
        html_list.append(html)

    else:
        if isinstance(ans, pd.Series):
            ans = ans.reset_index()
            return return_response_df(ans, response_id)
        else:
            return str(ans)

    return html_list






