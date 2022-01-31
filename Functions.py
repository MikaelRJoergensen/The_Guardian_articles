import requests
from bs4 import BeautifulSoup
import json


def get_data(query, from_date, to_date, query_fields, tag_type):
    """
    This function takes in all the parameters used to send the request call to The Guardians API’s. It will as for an API key. This is converted in to a JSON file and returns all the tags into a list

    Parameters
    ----------
    query : str
        Request content containing this str. 
    from_date : str
        The string which defines the start date you wish to get information from..
    to_date : str
        The string which defines the end period you wish to get information from..
    query_fields : str
        This strings specify in which indexed fields query terms should be searched on.
    tag_type : str
        This string determines what the media type, such as article, poll, video, etc will be retrieved.

    Returns
    -------
    data_list : list
        list of tags 

    """
    data_list = [] # List for article data
    apikey = input("Please enter your API key: ")
    
    # This is for getting the page number to iterate through
    query_url = f"https://content.guardianapis.com/search?" \
                f"api-key={apikey}" \
                f"&q={query}" \
                f"&query-fields={query_fields}" \
                f"&type={tag_type}" \
                f"&from-date={from_date}" \
                f"&to-date={to_date}" \
                f"&page-size=200&order-by=oldest" \

    r = requests.get(query_url)
    data = r.json()
    response = data["response"]
    pages = response["pages"]  

    # Getting the actual scrape from the API
    for i in range(1,pages+1): # Iterating through all pages in the API given the search criterias
        query_url = f"https://content.guardianapis.com/search?" \
                    f"api-key={apikey}" \
                    f"&q={query}" \
                    f"&query-fields={query_fields}" \
                    f"&type={tag_type}" \
                    f"&from-date={from_date}" \
                    f"&to-date={to_date}" \
                    f"&show-fields=headline,body,trailText&show-tags=keyword&page-size=200&order-by=oldest" \
                    f"&page={i}"

        response = requests.get(query_url)
        data = response.json() # Turns response into .json and stores it in the variable data
        results = data["response"]["results"] # Extracting the information that we need
        for i in range(len(results)): # Stores all tags and articles in a list
            data_list.append(results[i])
        
    return data_list


def article_info_dictionary_maker(headline, trail_text_clean, text, date,tag_list,webURL): 
    """
    Gets input from parsing_scrape and creates and stores the info in .json format

    Parameters
    ----------
    headline : str
        String from parsing_scrape headline.
    trail_text_clean : str
        String from parsing_scrape trail_text.
    text : str
        String from parsing_scrape text.
    date : str
        String from parsing_scrape date.
    tag_list : list
        String from parsing_scrape tag_list.
    webURL : str
        String from parsing_scrape webURL.

    Returns
    -------
    dict_articles : list
        List of dictionaries in .json format.

    """
    dict_articles = {} # Empty dictionary for appending article data
    dict_articles.update([('headline', headline), 
            ('trailtext', trail_text_clean),
            ('text', text),
            ('date',date),
            ('tags',tag_list),
            ('webUrl',webURL)]) # Creating the json structure with the data we need 
    return dict_articles

def parsing_scrape(data, L):
    """
    Parses headline, trail text, text, date, tag list and webURL and appends it to list L.

    Parameters
    ----------
    data : list
        A list containing results from Functions.get.data.
    L : list
        Use an empty list.

    Returns
    -------
    A list which contains the headline, trail text, text, date, tag list and webURL.

    """
    for i in range(0,len(data)): # Iterating through article data
        tag_list = []
        
        single_article_data = data[i]
        fields = single_article_data["fields"] # Making dictionary with fields = headline, body, trailText
        
        # Cleaning headline
        headline = fields['headline'] 
        
        # Cleaning trailText
        trail_text = fields["trailText"]
        soup = BeautifulSoup(trail_text,'html.parser')
        trail_text_clean = soup.get_text() 

        # Cleaning body
        body = fields["body"]
        soup_body = BeautifulSoup(body,'html.parser')
        text = soup_body.get_text()

        # Date
        date = single_article_data['webPublicationDate'][0:10] # Removing time of day from date format

        # Cleaning tags
        for j in range(0,len(single_article_data['tags'])):
            n = single_article_data['tags'][j]['id'].find("/") # Finding the chracters until the first /
            tag = single_article_data['tags'][j]['id'][0:n]  # Here we save the tag 
            if tag not in tag_list:
                tag_list.append(tag)


        # WebURL
        webURL = single_article_data["webUrl"]

        L.append(article_info_dictionary_maker(headline, trail_text_clean, text, date, tag_list, webURL))  
    return(L)

#%%
def storing_article_txt(L):
    """
    Use the list from Functions.parsing_scrape and store that data into a separate text files.

    Parameters
    ----------
    L : list
        List from Functions.parsing_scrape.

    Returns
    -------
    Every article in seperate text files.

    """
    for k in range (0,len(L)): # Iterating through list with article data and saving articles in txt.file
        fname = str(k)
        text = open('temp_data/articles/'+fname+".txt",'w',encoding="UTF-8")
        text.write("Headline: "+L[k]['headline']+"\n")
        text.write("Trail text: "+L[k]['trailtext']+"\n")
        text.write("Body: "+L[k]['text']+"\n")
        text.close()

def storing_data_json(L): # Saving the article + data in .json format
    """
    Use the list from Functions. parsing_scrape store that data into a JSON file

    Parameters
    ----------
    L : list
        List of dictionaries from Functions.parsing_scrape.

    Returns
    -------
    All articles in a JSON file.

    """
    with open('temp_data/data.json', 'w', encoding='utf-8') as f:
        json.dump(L, f, ensure_ascii=False, indent=2)