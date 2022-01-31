
# Importing functions
import Functions
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table as dt
import json
from datetime import datetime
import plotly.express as px
from wordcloud import STOPWORDS
from wordcloud import WordCloud  
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

#%%
# Scraping the API
data = Functions.get_data("Denmark", "2019-01-01", "2020-12-31", "body", "article")

# Parsing data
L = [] #Making an empty list to append the results of the function parsing_scrape
Functions.parsing_scrape(data, L)

# Storage
Functions.storing_article_txt(L)
Functions.storing_data_json(L)

#%%




# Loading .json file 
data_json = json.load(open('temp_data/data.json', encoding='UTF-8'))

# Changing the date column entries to datetime format
for article in data_json:
    d = article["date"]
    dt_obj = datetime.strptime(d, "%Y-%m-%d")
    article["date"] = dt_obj

#%%


# CREATES NESCESSARY GLOBAL VARIABLES

df_test = pd.DataFrame(data_json)
df_test['month_year'] = df_test['date'].dt.to_period('M') # Creating a new column with month and year of the articles
df_test['ids'] = df_test.index
tags = df_test.tags.explode().unique() # Finding all the unique tags from all articles
tags = [x for x in tags if str(x) != 'nan'] # Removing nan entries caused by articles without tags
options = [{'label':t,'value':t} for t in tags] # Stores tags as label and value in a list of dictionaries (for use in dropdown menu)

unique = df_test.month_year.unique() # Store all the unique timestamps
nmonth = len(df_test.month_year.unique()) # Store the number of unique timestamps as integer

# Creating a dataframe with columns for each month of the scrape with the number of times a tag has been used the given month
x = []
df_all = pd.DataFrame()
df_month = pd.DataFrame()
for i in range(0,nmonth):
    df_month = df_test[df_test.month_year == unique[i]]
    x.append(df_month.tags.explode().value_counts())
df_all = pd.concat(x,axis=1)


df_all = df_all.T.fillna(0) # nan represents a tag not being used, therefore changed to 0
df_all = df_all.set_axis(list(unique.astype(str))) # Setting months as rows and tags as columns


# DASH/PLOTLY
app = dash.Dash(__name__)

app.layout = dbc.Container([
    html.Br(),
    
    # Headline
    dbc.Row(
        dbc.Col(html.H1('The Guardian Articles Data Visulation'),
                    ),
            ),
    
    # Linechart + dropdown container
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id = 'graph1', figure = {},),
                    width={'size' : 10},
                    ),
            dbc.Col(
                [
                    html.P(children='Display frequency of a tag'),
                    dcc.Dropdown(id='tag',
                                 options= options,
                                 value='world',
                                 placeholder='Choose a tag',
                                 searchable=False,
                                 ),
                    ],width={'size' : 2}),
                ]),

    html.Br(),
    
    # Wordcloud title container
    dbc.Row([
    html.H2(id='Wordcloud_titel'),
    ]),

    # Wordcloud image container
    dbc.Row(
        dbc.Col(html.Img(id='graph2',style={'height':'100%', 'width':'100%'}),
           ), 
        ),  

    html.Br(),
    
    # Section headline for article search
    dbc.Row(
        dbc.Col(html.H2('Do you want to search for articles by tags or words in text or both?'), 
        )
    ),
    
    # Search bar and radio items
    dbc.Row([
        dbc.Col(
        dcc.Input(id='searchInputText', type = "search", placeholder="Search for tag or word", style={'width':'100%'}),
            width = 2
            ),
        dbc.Col(
        dcc.RadioItems(
                id='tagsOrWord_radioItem',
                options = [{'label': 'Search for tags and words', 'value': 'searchForBoth'},
                           {'label': 'Search by tags only', 'value': 'searchForTags'},
                           {'label': 'Search by words in text', 'value': 'searchForWords'}], 
                value = 'searchForBoth',
                inputStyle={"margin-left": 30}),
                    width = 10),
        ]),
    html.Br(),
    dcc.Store(id='tag_word'), #Here gemmer vi ouyput fra SearchInputText, så vi ikke får ekstra tekst under. 
    
    # Container search result articles
   
    dbc.Row([
        dbc.Col([
            dbc.Label('Click a cell in the table:'),
                dt.DataTable(
                    id='Search_result',
                    columns=[{"name":'Headline',"id":'headline'}],
                    
                    page_size = 10,
                    style_cell={'textAlign' :'left'},
                    style_data ={'whiteSpace': 'normal', 'height':'auto'},
                     
                    ),
                ], width = 6
          ),
      
    html.Br(),
    
        
         dbc.Col([
             dbc.Label('Click on recommended article table:'),
             dt.DataTable(
                  id='tbl',
                  columns=[{"name": 'Headline',"id":'headline'}],
                  page_size = 10,
                  style_cell={'textAlign' :'left'},
                  style_data ={'whiteSpace': 'normal','height':'auto'},
                  
                  
                  )],width = 6
             ),
        ],),
 
  dbc.Row([
      dbc.Row([
          dbc.Col(
          html.H3(id='article_headline')),
          dbc.Col(
          html.H3(id='recommended_article_headline'))
          
          ]),
      dbc.Row([
          dbc.Col(
          html.H5(id='article_trailtext')),
          dbc.Col(
          html.H5(id='recommended_article_trailtext')),

          ]),
      dbc.Row([
      dbc.Col(id='article'),
      dbc.Col(id='recommended_article'),
      ])
      ]),
    
   
    
])
   
#---------------------------- Line chart ----------------------------
@app.callback(
    dash.dependencies.Output(component_id='graph1',component_property='figure'),
    dash.dependencies.Input(component_id='tag',component_property='value')
    )
def update_Graph(tag):
    dff_all = df_all.copy()
    freq_input_tag = dff_all[tag]/df_all.sum(axis=1) # Calculating frequency
    
    fig = px.line(freq_input_tag,labels=dict(value='Frequency',index='Month-Year'),markers=True) # Creates line chart
    
    fig.layout.update(showlegend=False) # Removes the legend
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0)) # Removes the white space margein to the right

    return fig

#---------------------------- Wordcloud ---------------------------- 
@app.callback(
    dash.dependencies.Output(component_id='graph2',component_property='src'),
    dash.dependencies.Input(component_id='tag',component_property='value'))
def update_Graph2(tag):
    x = df_test.tags.explode().str.contains(tag) # All article texts with the chosen tag
    txt = ''.join(df_test.iloc[list(x[x == True].index)].text) # Joins the article texts
    buf = io.BytesIO() 
    stop_words = ["s", "said", "say", "U", "says", "will"] + list(STOPWORDS) # List of unwanted words
    wordcloud = WordCloud(stopwords=stop_words, background_color='#e5ecf7',width=1600, height=800).generate(txt) # Generates wordcloud
    plt.figure( figsize=(40,30)) # Resolution
    plt.imshow(wordcloud, interpolation='bilinear') # Stores wordcloud as matplotlib 
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(buf, format = "png",bbox_inches='tight') # Saves wordcloud as an image
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # Encode to html elements
    return "data:image/png;base64,{}".format(data)

#---------------------------- Search bar input ----------------------------
@app.callback(Output("tag_word","children"),Input("searchInputText", "value"))
def update_inputOfSearchWord(searchInput):
    searchStr = searchInput.lower()
    return searchStr

#---------------------------- Data frame search results ----------------------------
@app.callback(
    Output(component_id = "Search_result", component_property = "data"),
    [Input(component_id = "tagsOrWord_radioItem", component_property = "value"),
     Input(component_id= "tag_word", component_property = "children")])
def update_radioButton(decision_from_radio,txt_tag):
    
    # Search function
    y2 = df_test.text.explode().str.contains(txt_tag) # Finds article text containing search word
    x2 = df_test.tags.explode().str.contains(txt_tag) # Finds articles containing tags from search word
    y3 = df_test.iloc[list(y2[y2 == True].index)] # Returns the part of the dataframe where the text is found
    x3 = df_test.iloc[list(x2[x2 == True].index)] # Returns the part of the dataframe where tag is found
    y3['TW']=0 # Indicates if article is found with text
    x3['TW']=1 # Indicates if article is found with tag
    w = (pd.concat([x3,y3])).drop_duplicates(subset='text') # Concatenate dataframes with found articles and drops duplicates
    w['id'] = w.index
    
    # Radio button selection
    if decision_from_radio == "searchForTags":
        Search_output = w[w['TW'] == 1]
    elif decision_from_radio == "searchForWords":
        Search_output = w[w['TW'] == 0]
    else:
        Search_output = w
       
    Search_output = Search_output[['headline','trailtext','id']].to_dict('records') # Datatable of searched articles' headline and trailtext
    return Search_output

#---------------------------- Show searched article ----------------------------
# Shows the chosen article headline, trailtext and text 
@app.callback([Output('article','children'), 
               Output('article_headline','children'),
               Output('article_trailtext','children')],
              Input('Search_result','active_cell')
               ) 
def show_article(article):
    return df_test[df_test['ids'] == article['row_id']].text,df_test[df_test['ids'] == article['row_id']].headline,df_test[df_test['ids'] == article['row_id']].trailtext

#---------------------------- Show data table with recommended articles ----------------------------
@app.callback(Output('tbl','data'), Input('Search_result','active_cell'))
def show_recommended_table(art_no1):
    art_no1 = art_no1['row_id']
    input_tag = df_test.tags.iloc[art_no1]
    input_tag_date = df_test.date.iloc[art_no1]
    Num_rec_return = 100
    
    # Creates datatable 'matches' with appropriate dimensions
    matches = pd.DataFrame(pd.np.empty((len(df_test.tags), 4)) * pd.np.nan,columns=['Intersect','Number_of_matches','article_Date','Timedelta'])

    # Loops through dataframa and finds articles
    for k in range (0,len(df_test.tags)):
        intersect = list(set(input_tag).intersection(set(df_test.tags.iloc[k]))) # Finds intersect between searched tag and the set of tags
        nintersect = len(intersect) # Number of matched articles with tag
        
    # (The rest of this function): If number of intersects is zero, then the tag has no match with the tags in articles and articles returned
    # are sorted by nearest smallest absolute timedifference. If number of intersects are strictly larger than zero
    # it returns articles prioritized by number of matches of tags and secondly absolute timedifferences.
        if nintersect !=0: 
            matches['Intersect'].iloc[k] = intersect
            matches['Number_of_matches'].iloc[k] = nintersect 
            matches['article_Date'].iloc[k] = df_test.date.iloc[k]
        else: 
            matches['article_Date'].iloc[k] = df_test.date.iloc[k]

    matches['Timedelta'] = abs(input_tag_date -matches.article_Date.dropna())
    matches = matches.sort_values(['Number_of_matches','Timedelta'],ascending = [False,True])
    matches = matches[['Number_of_matches','Timedelta']]
    matches = matches[0:Num_rec_return+1]

    match_text = df_test.iloc[matches.index]
    match_text['id'] = match_text.index
    match_text = match_text[1:]
    rec_art = match_text[['trailtext','headline','text','id']].to_dict('records')
    
    return rec_art

#---------------------------- Show recommended article ----------------------------
# Shows the chosen article headline, trailtext and text
@app.callback ([Output(component_id = 'recommended_article', component_property = 'children'),
                Output(component_id = 'recommended_article_headline', component_property = 'children'),
                Output(component_id = 'recommended_article_trailtext', component_property = 'children')
                ],(Input('tbl','active_cell')))
def show_recommended_article(click):
    return df_test[df_test['ids'] == click['row_id']].text,df_test[df_test['ids'] == click['row_id']].headline,df_test[df_test['ids'] == click['row_id']].trailtext

#---------------------------- Showing the chosen tag in wordcloud header ----------------------------
@app.callback(Output('Wordcloud_titel','children'),Input('tag','value'))  
def wordcloud_titel(titel):
    
    return 'A Wordcloud of articles tagged with: '+titel

if __name__ == '__main__':
    app.run_server(debug=False)
