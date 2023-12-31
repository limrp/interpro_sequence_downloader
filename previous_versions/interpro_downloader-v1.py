#!/usr/bin/env python3

# *--------------------------------------------------------------------------------------------------------
# | PROGRAM NAME: 
# | DATE: 
# | VERSION: 2
# | CREATED BY: Lila Maciel Rodriguez Perez
# | PROJECT FILE: 
# | GITHUB REPO:
# *--------------------------------------------------------------------------------------------------------
# | INFO: - This version use generators to be more memory-efficient when handling big fasta files.
# |       - This program doesn't use Biopython. That version will come later.
# *--------------------------------------------------------------------------------------------------------
# | PURPOSE: Filtering sequences by the length specified by the user
# *--------------------------------------------------------------------------------------------------------
# | USAGE:  
# | - With a file:
# |   python3 filter_seqs_by_length.py -i input.fasta -m 100 -o output.fasta
# | - With standard input:
# |   cat input.fasta | python3 filter_seqs_by_length.py -i - -m 100 -o output.fasta
# |   pigz input.fasta.gz | python3 filter_seqs_by_length.py -i - -m 100 -o output.fasta
# *--------------------------------------------------------------------------------------------------------
# | WARNING: 
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

def interpro_accession_classifier(accession_file: str) -> Dict[str, List[str]]:

    categories = {
            'cdd': [],
            'InterPro': [],
            'ncbifam': [],
            'panther': [],
            'pfam': [],
            'prints': [],
            'profile': [],
            'prosite': [],
            'smart': []
            }
    
    with open(accession_file, mode = "r") as fh:
        for line in fh:
            line_list = line.rstrip().split("\t")
            accession = line_list[0]

            if accession.startswith("cd"):
                categories['cdd'].append(accession)
            elif accession.startswith("IPR"):
                categories['InterPro'].append(accession)
            elif accession.startswith(("NF", "TIGR")):
                categories['ncbifam'].append(accession)
            elif accession.startswith("PTHR"):
                categories['panther'].append(accession)
            elif accession.startswith("PF"):
                categories['pfam'].append(accession)
            elif accession.startswith("PR"):
                categories['prints'].append(accession)
            elif accession.startswith("PS"):
                categories['prosite'].append(accession)
            elif accession.startswith("SM"):
                categories['smart'].append(accession)
            else:
                # print(f"No category: {accession}")
                pass
    
    return categories


def interpro_api_sequence_downloader(db, accession, output_fasta, error_file):
    # Configure logging
    # logging.basicConfig(
    #     filename = 'api_script.log', level = logging.DEBUG, 
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     datefmt='%Y-%m-%d, %H:%M:%S'
    #     )

    # Creating an object 
    # logger = logging.getLogger(__name__)

    BASE_URL = f"https://www.ebi.ac.uk:443/interpro/api/protein/UniProt/entry/all/{db}/{accession}/?page_size=200&extra_fields=sequence"

    HEADER_SEPARATOR = "|"
    LINE_LENGTH = 80

    context = ssl._create_unverified_context()

    next = BASE_URL
    last_page = False # flag

    attempts = 0
    protein_count = ""

    # Counter of sequences
    c = 0

    # Initialize an empty set to store seen sequences
    seen_sequences = set()  
    seen_ids = set()

    # while next is not null (None) or empty
    while next:
        #c += 1
        #print(f"$ Iteration number {c}")

        try:
            req = request.Request(next, headers={"Accept": "application/json"})
            res = request.urlopen(req, context=context) #===> If there is an HTTP error here, go to the except block

            # If the API times out due a long running query
            if res.status == 408:
                #print(f"Response status 408: The API timed out! Sleep a bit and continue.")
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
                #print(f"value of next: {next}")
                last_page = True
        
        except HTTPError as error:
            #print(f"An HTTP Error!")

            if error.code == 408:
                #print(f"HTTP Error 408!")
                sleep(61)
                continue
            else:
                # If there is a different HTTP error, it wil re-try 3 times before failing
                if attempts < 3:
                    #print(f"An HTTP error different than 408! e: {error.code}. Starting attempt number {attempts}")
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
                    #print(f"entries header: {entries_header}")

                    # Increasing the counter
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

                # Checking for duplicated ID's and sequences
                # if id in seen_ids:
                #     print(f"Duplicate ID found for accession {item['metadata']['accession']}, {id}")
                # else:
                #     seen_ids.add(id)
                
                # # Checking for duplicated ID's
                # if seq in seen_sequences:
                #     # Print a message with the first 20 characters of the duplicate sequence
                #     print(f"Duplicate sequence found for accession {item['metadata']['accession']}, {id}: {seq[:10]}...")
                # else:
                #     # Add the sequence to the set of seen sequences
                #     seen_sequences.add(seq)
                
                # if (id in seen_ids and seq in seen_sequences):
                #     print(f"Duplicate ID and sequence found for accession {item['metadata']['accession']}, {id}")
                # Checking finished

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

    # Classify accessions
    accessions_dict = interpro_accession_classifier(args.input)

    # Iterating over db_key and list_accessions value in dictionary
    for db_key, accession_list in accessions_dict.items():
        for i, accession in enumerate(accession_list, start = 1):
            print(f"\n$ Accession number {i}: {accession} from the {db_key.upper()} database")
            interpro_api_sequence_downloader(db=db_key, accession=accession, output_fasta=args.output, error_file=args.error)
            print("\n")

# Execute the main function only if the script is run directly (not imported as a module)
if __name__ == "__main__":
    main()