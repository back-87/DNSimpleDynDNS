#!/usr/bin/env python3
import json

from dnsimple import Client
from typing import Union
from requests import get
from dnsimple.struct.zone_record import ZoneRecord, ZoneRecordInput, ZoneRecordUpdateInput

import Constants

client: Union[Client, None] = None
account_id = 0

def main():
    init()
    update_ip_for_all_domains()

def init():
    # Constants.py not tracked by git, create that file and add the string var
    global client, account_id
    client = Client(access_token=Constants.DNSIMPLE_ACCESS_TOKEN)
    account_id = client.accounts.list_accounts().data[0].id
    if account_id is None or account_id == 0:
        print(f"There was a problem getting the account id. Please check access_token. Exit")
        return False

def update_ip_for_all_domains():
    public_ip = get('https://api.ipify.org').content.decode('utf8')

    if len(public_ip) < 8:
        print(f"There was a problem getting the public ip of this machine. Got {public_ip}. Exit")
        return False

    if client is None:
        print("Initialization failed, can't continue. Check Constants.DNSIMPLE_ACCESS_TOKEN. Exit")
        return False

    print(f"Client initialized, iterating domains and updating IPs to {public_ip}")
    domain_page = 1
    zone_page = 1
    domain_response = client.domains.list_domains(account_id, domain_page)

    while domain_response is not None and domain_page <= domain_response.pagination.total_pages:

        for domain_record in domain_response.data:
            zone_response = client.zones.list_records(account_id, domain_record.name, page=zone_page)

            while zone_response is not None and zone_page <= zone_response.pagination.total_pages:
                print(f'zone_page: {zone_page} - zone_total: {zone_response.pagination.total_pages}')

                for zone_record in zone_response.data:
                    if zone_record.type == "A" and zone_record.content != public_ip:
                        print(f'A record needs updating, old IP: {zone_record.content} ({zone_record.id})')
                        mutable_record_dict = {
                            "content": public_ip,
                            "ttl": 300,
                            "name": "",
                            "priority": 0,
                            "regions": ["global"],
                            "type": "A",
                            "id": zone_record.id
                        }

                        response = client.zones.update_record(account_id, domain_record.name, zone_record.id, ZoneRecordUpdateInput(name=zone_record.name, content=public_ip, ttl=600, priority=100))
                        print(f'update response: {response.http_response}')
                    elif zone_record.type == "A":
                        print(f'record type A, but the IP is current. No need to update: - {zone_record.content} ({zone_record.id})')
                    else:
                        print(f'encountered record of type: ({zone_record.type}), ignoring')

                zone_page += 1
                zone_response = client.zones.list_records(account_id, domain_record.name, page=zone_page)

        print(f'domain_page: {domain_page} - domain_total: {domain_response.pagination.total_pages}')
        domain_page += 1
        domain_response = client.domains.list_domains(account_id, domain_page)


if __name__=="__main__":
    main()

