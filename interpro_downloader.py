#!/usr/bin/env python3

# *--------------------------------------------------------------------------------------------------------
# | PROGRAM NAME: Interpro Sequence Downloader
# | DATE: 08/09/2023
# | VERSION: 2
# | CREATED BY: Lila Maciel Rodriguez Perez using INTERPRO snippet
# | PROJECT FILE: 
# | GITHUB REPO: https://github.com/limrp/interpro_sequence_downloader
# *--------------------------------------------------------------------------------------------------------
# | INFO: - This version of the script was built upon the code snippet generated by the INTERPRO team to download 
# |         a large amount of sequences programmatically rather than through the web browser.
# |       - More information: https://www.ebi.ac.uk/interpro/result/download/#/entry/InterPro/|accession
# |       - This program doesn't use Biopython.
# *--------------------------------------------------------------------------------------------------------
# | PURPOSE: Download all the proteins associated with the interpro accessions provided by the user.
# *--------------------------------------------------------------------------------------------------------
# | USAGE:  
# | interpro_downloader.py [-h] --input INPUT_ACCESSION_LIST.TXT --output OUTPUT.FASTA --error ERROR.TXT
# | Get your accession list here: https://www.ebi.ac.uk/interpro/search/text/
# *--------------------------------------------------------------------------------------------------------

# *-------------------------------------  Libraries ------------------------------------------------------*
# standard library modules
import sys, errno, re, json, ssl
from urllib import request
from urllib.error import HTTPError
from time import sleep
# Classifier function
from typing import List, Dict
from pprint import pprint

import argparse
from pathlib import Path
# *--------------------------------------* Defining functions *--------------------------------------------*

def interpro_credits():
    return print("""
    \n
    This version of the script was written by Lila Maciel Rodriguez Perez and was built upon the code snippet 
    generated by the INTERPRO team to download a large amount of sequences programmatically rather than through 
    the web browser.
    For more information, visit: https://www.ebi.ac.uk/interpro/result/download/#/entry/InterPro/|accession
    Get your accession list here: https://www.ebi.ac.uk/interpro/search/text/
    \n
    """)

def interpro_accession_classifier(accession_file: str) -> Dict[str, List[str]]:

    categories = {
            'cdd': [],
            'cathgene3d': [],
            'InterPro': [],
            'ncbifam': [],
            'panther': [],
            'pfam': [],
            'pirsf': [],
            'prints': [],
            'profile': [],
            'prosite': [],
            'smart': [],
            'ssf': []
            }
    
    with open(accession_file, mode = "r") as fh:
        for line in fh:
            line_list = line.rstrip().split("\t")
            accession = line_list[0]

            if accession.startswith("cd"):
                categories['cdd'].append(accession)
            elif accession.startswith("G3DSA"):
                categories['cathgene3d'].append(accession)
            elif accession.startswith("IPR"):
                categories['InterPro'].append(accession)
            elif accession.startswith(("NF", "TIGR")):
                categories['ncbifam'].append(accession)
            elif accession.startswith("PTHR"):
                categories['panther'].append(accession)
            elif accession.startswith("PF"):
                categories['pfam'].append(accession)
            elif accession.startswith("PIRSF"):
                categories['pirsf'].append(accession)
            elif accession.startswith("PR"):
                categories['prints'].append(accession)
            elif accession.startswith("PS"):
                categories['prosite'].append(accession)
            elif accession.startswith("SM"):
                categories['smart'].append(accession)
            elif accession.startswith("SSF"):
                categories['ssf'].append(accession)
            else:
                pass
    
    return categories


def interpro_api_sequence_downloader(db, accession, output_fasta, error_file):

    # BASE_URL = f"https://www.ebi.ac.uk:443/interpro/api/protein/UniProt/entry/all/{db}/{accession}/?page_size=200&extra_fields=sequence"
    BASE_URL = f"https://www.ebi.ac.uk:443/interpro/api/protein/UniProt/entry/{db}/{accession}/?page_size=200&extra_fields=sequence"

    HEADER_SEPARATOR = "|"
    LINE_LENGTH = 80

    context = ssl._create_unverified_context()

    next = BASE_URL
    last_page = False # flag

    attempts = 0
    protein_count = ""

    # Counter of proteins
    c = 0

    # while next is not null (None) or empty
    while next:

        try:
            req = request.Request(next, headers={"Accept": "application/json"})
            res = request.urlopen(req, context=context) #===> If there is an HTTP error here, go to the except block

            # If the API times out due a long running query
            if res.status == 408:
                # wait just over a minute
                sleep(61)
                # then continue this loop with the same URL
                continue #=> jumps back to the beginning of the loop (without updating the next (url) variable).
            elif res.status == 204:
                # no data so leave loop
                #print(f"Response status 204: no data! Leaving the loop ...")
                break

            # JSON response (body or content) from the API => payload  
            payload = json.loads(res.read().decode())
            # Updating next variable with the new URL for pagination.
            next = payload["next"]
            # print(f"next url: {next}")
            # Getting value of count key
            protein_count = payload["count"]
            #print(f"Number of proteins: {pt_count}")

            # If, after some errors and attemps, it reached here then
            # Reset attempts to 0
            attempts = 0
            # If this is the last page, i.e. next is null, update last_page flag
            if not next:
                last_page = True
        
        except HTTPError as error:

            if error.code == 408:
                sleep(61)
                continue
            else:
                # If there is a different HTTP error, it wil re-try 3 times before failing
                if attempts < 3:
                    attempts += 1
                    sleep(61)
                    continue
                else:
                    with open(file = error_file, mode = "a") as error_fh:
                        error_fh.write(f"Failed to download data for accession: {accession}")
                        error_fh.write(f"Last URL: {next}\n")

                    #raise error
                    return

        # After the request is made and if there were no errors (or if all errors were handled)
        # Open a file in write mode to store the sequences
        with open(file = output_fasta, mode='a') as fasta_file:
            
            for i, item in enumerate(payload["results"]):

                # item = result = dictionary
                entries = None
                if ("entry_subset" in item):
                    entries = item["entry_subset"]
                elif ("entries" in item):
                    entries = item["entries"]

                if entries is not None:
                    entries_header = "-".join(
                        [entry["accession"] + "(" + ";".join(
                            [
                                ",".join(
                                    [ str(fragment["start"]) + "..." + str(fragment["end"]) 
                                    for fragment in locations["fragments"]]
                                    ) for locations in entry["entry_protein_locations"]
                                    ]
                                    ) + ")" for entry in entries]
                                    )

                    # Increasing the counter of proteins
                    c += 1
                    print(f"# Result {c}: Protein {c}/{protein_count} for accession {accession}")

                    id = ('>' + item["metadata"]["accession"] + HEADER_SEPARATOR + 
                            entries_header + HEADER_SEPARATOR + 
                            item['metadata']['name'])
                    print(f"Protein ID: {id[1:]}")

                    fasta_file.write(">" + item["metadata"]["accession"] + HEADER_SEPARATOR
                                        + entries_header + HEADER_SEPARATOR
                                        + item["metadata"]["name"] + "\n")

                else:
                    fasta_file.write(">" + item["metadata"]["accession"] + HEADER_SEPARATOR 
                                        + item["metadata"]["name"] + "\n")

                seq = item["extra_fields"]["sequence"]

                fastaSeqFragments = [seq[0+i:LINE_LENGTH+i] for i in range(0, len(seq), LINE_LENGTH)]
                
                for fastaSeqFragment in fastaSeqFragments:
                    fasta_file.write(fastaSeqFragment + "\n")

            # Don't overload the server, give it time before asking for more
            if next:
                sleep(1)
    
    print(f"*~~ Finished downloading proteins associated with accession {accession}. ~~*")
    print(f"*~~ The accession {accession} had {protein_count} associated proteins that should have been downloaded.~~*")
    print(f"*~~ The number of proteins downloaded was {c}.~~*")

# *--------------------------------------* Primary logic of the script *------------------------------------*
def main():
    parser = argparse.ArgumentParser()
    # accession file, output fasta, error file
    parser.add_argument('--input', '-i', type=str, required=True, help='File with list of accessions.')
    parser.add_argument('--output', '-o', type=str, required=True, help='The output FASTA file.')
    parser.add_argument('--error', '-e', type=str, required=True, help='File with accessions that could not be downloaded.')
    args = parser.parse_args()

    # Defining the paths to the files
    file_path1 = Path(args.output)
    file_path2 = Path(args.error)
    # Checking if both files exist
    if file_path1.exists() or file_path2.exists():
        print("The output or the error file already exist. Please rename or move the files before proceeding.")
        # Exit the script gracefully
        exit()

    # Classify accessions by database
    accessions_dict = interpro_accession_classifier(args.input)

    # Iterating over db_key and list_accessions value in dictionary
    for db_key, accession_list in accessions_dict.items():
        for i, accession in enumerate(accession_list, start = 1):
            print(f"\n$ Accession number {i}: {accession} from the {db_key.upper()} database")
            interpro_api_sequence_downloader(db=db_key, 
                                            accession=accession, 
                                            output_fasta=args.output, 
                                            error_file=args.error
                                            )
            print("\n")
            
    print("*~~* Download finished *~~*")
    # Credits to the interpro team for the main code snippet that retrieves data from the API
    interpro_credits()

# Execute the main function only if the script is run directly (not imported as a module)
if __name__ == "__main__":
    main()
