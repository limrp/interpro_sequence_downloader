# InterPro Downloader

## Description

The `interpro_downloader.py` script is a Python utility that facilitates the batch downloading of sequences associated with a list of specified accessions from the InterPro database. The script takes a file with a list of accessions as input and downloads the related sequences, saving them to a specified output FASTA file. Additionally, it logs any accessions that could not be downloaded to a specified error file.

This script was built upon the code snippet provided by the INTERPRO team to facilitate the programmatic download of large quantities of sequences, as opposed to doing it through a web browser. It serves as a useful tool for managing and analyzing large datasets efficiently.

For further information, please visit:
- [InterPro Result Download](https://www.ebi.ac.uk/interpro/result/download/#/entry/InterPro/|accession) - where you can find details on downloading results based on specific accessions.
- [InterPro Text Search](https://www.ebi.ac.uk/interpro/search/text/) - a platform where you can generate an accession list using various query terms or keywords.

We hope this tool aids you in your research and data analysis tasks. Feel free to reach out with any questions or suggestions!


## Requirements

- Python 3.x

## Usage

```bash
python3 interpro_downloader.py -h
```

### Arguments

```
-h, --help            : Show this help message and exit
--input INPUT, -i INPUT : File with list of accessions
--output OUTPUT, -o OUTPUT : The output FASTA file where the sequences will be saved
--error ERROR, -e ERROR : File to log accessions that could not be downloaded
```

## Installation

1. Ensure you have Python 3.x installed on your system.
2. Download the `interpro_downloader.py` script to your local system.

## Running the Script

Navigate to the directory where the script is located and use the following command to run the script:

```bash
python3 interpro_downloader.py --input <input_file> --output <output_file> --error <error_file>
```

Replace `<input_file>`, `<output_file>`, and `<error_file>` with your actual file paths.

## Support

For any issues or suggestions, please contact `limrod.15@gmail.com`.

## License


