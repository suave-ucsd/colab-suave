import requests
import re
from urllib.parse import urlparse
from IPython.display import Markdown, display
import ipywidgets as widgets
import zipfile
import io

def printmd(string):

    display(Markdown(string))

def create_survey( survey_url,
                   new_file,
                   survey_name,
                   dzc_file,
                   user,
                   csv_file,
                   view,
                   views,
                   iflocal = "Load survey file from SuAVE" ):

    referer = survey_url.split("/main")[0] +"/"
    upload_url = referer + "uploadCSV"
    new_survey_url_base = survey_url.split(user)[0]

    csv = {"file": open(new_file, "rb")}
    upload_data = {
        'name': survey_name,
        'dzc': dzc_file,
        'user': user,
    }

# read the current survey file, if this is suave2
# example: http://suave2.sdsc.edu/getSurveyDzc?user=zaslavsk&file=Alianza_2_5_21
    if True: #urlparse(survey_url).netloc == 'suave2.sdsc.edu':
        if (iflocal == "Load survey file from SuAVE"):
            urlold = urlparse(survey_url).scheme+"://"+ urlparse(survey_url).netloc+'/getSurveyDzc?user='+user+'&file='+csv_file[len(user)+1:-4]
            import json
            rs=requests.get(urlold).json()
            s2views = rs['views']    
            upload_data.update( {'views' : s2views} )
        else:
            upload_data.update({'views' : ['grid', 'bucket', 'crosstab', 'jupyter']} )
            upload_data.update({'view' : 'grid'} )
    else:
        if (iflocal == "Import a local CSV file"):
            upload_data.update({'views' : '1110001'} )
            upload_data.update({'view' : 'grid'} )

    headers = {
        'User-Agent': 'suave user agent',
        'referer': referer
    }

    r = requests.post( referer + "getSurveyInfoByDzc",
                       data = {
                           "user": user,
                           "dzc": dzc_file,
                       },
                       headers = headers )

    has_netvis = False
    for j in r.json():

        if has_netvis:

            break
        
        if "netvis" in j.keys():

            for nv in j["netvis"]:

                if nv["type"] == "file":

                    nv_url = nv["url"]
                    nv_r = requests.get( nv_url, headers = headers )
                    
                    if nv_r.status_code == 200:
                        
                        netvis = nv_r.json()
                        has_netvis = True
                        break

    if has_netvis:

        zip_data = io.BytesIO()

        with zipfile.ZipFile( zip_data,
                              mode='w',
                              compression = zipfile.ZIP_DEFLATED ) as zf:

            zf.writestr( "new.csv", csv["file"].read() )
            zf.writestr( "new.json", json.dumps( netvis ) )

        zip_data.seek( 0, io.SEEK_SET )
        csv = { "corpus_db_zip": zip_data }
        
    r = requests.post( upload_url,
                       files = csv,
                       data = upload_data,
                       headers = headers )

    if r.status_code == 200:

        printmd("<b><span style='color:red; font-size: 200%;'>New survey created successfully</span></b>")
        regex = re.compile('[^0-9a-zA-Z_]')
        s_url = survey_name
        s_url =  regex.sub('_', s_url)

        if urlparse(survey_url).netloc == 'suave2.sdsc.edu':
            url = new_survey_url_base + user + "_" + s_url + ".csv" + "&view=" + view
        else:
            url = new_survey_url_base + user + "_" + s_url + ".csv" + "&views=" + views + "&view=" + view

        printmd("<b><span style='color:red; font-size: 200%;'>Click the URL to open the new survey</span></b>")
        printmd( f"<br><a href='{url}' target='_blank'>{url}</a>" )
    else:
        printmd("<b><span style='color:red; font-size: 200%;'>Error creating new survey.</span><span style='color:red; font-size: 120%;'> Check if a survey with this name already exists. Make sure you are logged into your SuAVE account.</span></b>")
        printmd("<b><span style='color:red'>Reason: </span></b>"+ str(r.status_code) + " " + r.reason)
        
def save_csv_file(df, absolutePath, csv_file):

    # new filename
    new_file = absolutePath + csv_file[:-4]+'_v1.csv'
    printmd("<b><span style='color:red'>A new temporary file will be created at: </span></b>")
    print(new_file)
    df.to_csv(new_file, index=None)
    return new_file


