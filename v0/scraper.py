# scrapes odds from ifortuna.cz and updates github datapackages

import csv
import datapackage  # v0.8.3
import datetime
import os
import requests

import ifortuna_cz_scraper_utils as utils
import settings

data_path = "data/"  # from this script to data

# repo settings

total_groups = 0
for fdir in settings.fortuna_dirs:
    data = utils.scrape_dir(fdir)
    date = datetime.datetime.utcnow().isoformat()
    for group in data:
        # load or create datapackage
        try:
            # load datapackage
            datapackage_url = settings.project_url + data_path + group['identifier'] + "/datapackage.json"
            dp = datapackage.DataPackage(datapackage_url)
        except:
            # create datapackage
            dp = datapackage.DataPackage()
            urldp = settings.project_url + "datapackage_prepared.json"
            rdp = requests.get(urldp)
            prepared = rdp.json()
            dp.descriptor['identifier'] = group['identifier']
            dp.descriptor['name'] = "ifortuna_cz_" + group['identifier']
            dp.descriptor['title'] = group['title'] + " - odds from ifortuna.cz"
            description = "Scraped odds from ifortuna.cz for: " + group['title'] + "; " + group['title_comment']
            dp.descriptor['description'] = description.strip().strip(";")
            dp.descriptor['description'] += " (" + group['title_bet'] + ")"
            for k in prepared:
                dp.descriptor[k] = prepared[k]
            if not os.path.exists(settings.git_dir + data_path + group['identifier']):
                os.makedirs(settings.git_dir + data_path + group['identifier'])
            with open(settings.git_dir + data_path + group['identifier'] + '/datapackage.json', 'w') as fout:
                fout.write(dp.to_json())
            with open(settings.git_dir + data_path + group['identifier'] + '/odds.csv', "w") as fout:
                header = []
                for resource in dp.resources:
                    if resource.descriptor['name'] == 'odds':
                        for field in resource.descriptor['schema']['fields']:
                            header.append(field['name'])
                dw = csv.DictWriter(fout, header)
                dw.writeheader()

        with open(settings.git_dir + data_path + group['identifier'] + '/odds.csv', "a") as fout:
            header = []
            for resource in dp.resources:
                if resource.descriptor['name'] == 'odds':
                    for field in resource.descriptor['schema']['fields']:
                        header.append(field['name'])
            dw = csv.DictWriter(fout, header)
            for row in group['rows']:
                i = 0
                for bet in row['bets']:
                    attributes = ['date', 'title', 'result', 'odds', 'date_bet', 'identifier']
                    item = {
                        'date': date,
                        'title': row['title'],
                        'result': group['bets'][i],
                        'odds': bet,
                        'date_bet': row['date_bet'],
                        'identifier': row['identifier'],
                    }
                    i += 1
                    dw.writerow(item)

    total_groups += len(data)
