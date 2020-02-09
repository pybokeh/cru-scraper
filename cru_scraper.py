from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
from requests_html import HTMLSession
from typing import TypeVar
import os
Session = TypeVar('requests_html.HTMLSession')


def getCruSession(user: str, password: str, url: str) -> Session:
    """Establish a persistent session with the CRU web site
    
    Parameters
    ----------
    user : str
        username
    password : str
        password
    url : str
        url to log into the CRU site
        
    Returns
    -------
    HTMLSession
    
    """
    
    payload = {
        'Username': user,
        'Password': password,
        'ufprt': 'CAF8477BDE81160B023359032A131EBA8ED2EFCCA369B1D4406ABA090A186F53D289629E6B2901EADF92F7200C4504C4EC8DA6A8AE05FD4C6298C6E3A5B090CF7AFEEC6E47030ACB04698860352BD8EA3914830C3D6099400102E9B87AD1389C568A810357BDE2D5BF115952F6B1B1D8C4E8783B',
        'RememberMe': 'false'
    }
    
    session = HTMLSession()
    
    res = session.post("https://cruonline.crugroup.com/login", data=payload)
    assert res.status_code == 200
    
    # POST a different ufprt value so that if site detects that another user has logged on,
    # we force a log off
    logoff_payload = {
        'ufprt': '7674E654A97C61E8335D82E3E72CB21E3B8BC67B82C4A2C28B5359C474B3E5AFAAD640D57AE7CC8A40515A37EF5740681F41C249B2F85397D86C2560F38BD27A43B4401FFB761DFEB88F3E34BAC675CA9AEADA14AD076EB02A85EAADD50D4678BE783B30BF67E11B6394BEE63C522175658A6BAD34B4EEA8982EC0C59790667556CC29D0'
    }
    res_final = session.post("https://cruonline.crugroup.com/login", data=logoff_payload)
    assert res_final.status_code == 200
    
    return res_final.session


def getCruXl(session: Session, url: str) -> None:
    """Download the CRU Excel file to the "data" folder
    
    Parameters
    ----------
    session : HTMLSession
        CRU session
    url : str
        The "Downloads" url
        
    Returns
    -------
    None
    """
    
    with session as s:
        try:
            res = s.get(url)
            assert res.status_code == 200
            
            month = datetime.now().strftime("%B").lower()
            year = datetime.now().strftime("%Y")
            yyyy_mm_dd = datetime.now().strftime("%Y-%m-%d")

            found = False 
            # Check if the current month's Excel file exists:
            for link in res.html.absolute_links:
                if f"steel-monitor-{month}-{year}-prices.xlsx" in link:
                    found = True
                    excel_url = link
                else:
                    pass
            print(f"Downloading Excel file from: {excel_url}")

            # If current month's Excel file is not found, then get the url for previous month
            if not found:
                prev_month = (datetime.now() + relativedelta(months=-1)).strftime("%B").lower()
                prev_year = (datetime.now() + relativedelta(months=-1)).strftime("%Y")
                for link in res.html.absolute_liks:
                    if f"steel-monitor-{prev_month}-{prev_year}-prices.xlsx" in link:
                        excel_url = link
                print(f"Downloading Excel file from: {excel_url}")

            # Make a REQUEST for the Excel file
            res_xl = s.get(excel_url, stream=True)
            assert res_xl.status_code == 200

            print('Checking if storage location exists...')
            save_directory = Path('data')

            # Check if "data" folder exists: if not, do nothing, else save Excel file
            if not save_directory.exists():
                print('Storage location does not exist.  Excel file will not be downloaded.')
            else:
                print('Storage location found.  Downloading Excel file...')
                # Stream the Excel file 1MB at a time ("lazy loading") to the file system
                with open(save_directory / f"cru_steel_prices-{yyyy_mm_dd}.xlsx","wb") as excel:
                    for chunk in res_xl.iter_content(chunk_size=1024):
                        # writing one chunk at a time to excel file
                        if chunk:
                            excel.write(chunk)
                print("Finished downloading Excel file")
        except Exception as e:
            print("Error - Could not download the Excel file: ", e)
        finally:
            # Log out of the site
            r = session.get('https://cruonline.crugroup.com/logout')
            assert r.status_code == 200

if __name__ == '__main__':
    user = os.environ['USERNAME']
    password = os.environ['PASSWORD']

    login_session = getCruSession(user, password, "https://cruonline.crugroup.com/login")
    getCruXl(login_session, "https://cruonline.crugroup.com/steel/monitor/downloads/")