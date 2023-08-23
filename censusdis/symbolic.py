# Copyright (c) 2022 Darren Erik Vengroff

"""
Utilities for creating symbolic names.

This module processes data sets from the US Census
and their respective symbolic names for
documentation purposes.
"""

import argparse
import censusdis.data as ced
from pathlib import Path

class symbolic:
    """
    A generator of datasets' symbolic names file.

    This creates symbolic names for datasets based on
    dataset names. The symbolic names are stored as 
    dictionary keys with values of the dataset names
    and url.

    Users will use this to generate most up to date
    dataset documentation file.
    """
    def __init__(self):
        self.dictionary = {}
        self.module_message = "# Copyright (c) 2022 Darren Erik Vengroff\n" + '\n"""\n' + "This module contains abbreviated names for commonly used data sets.\n" + "\nThese are typically used as the first argument to :py:func:`censudis.data.download`.\n" + "\nThere are a lot more data sets available than there are symbolic names here.\n" + "\nBut you can always use raw strings. For example, even for `ACS5` you can use\n" + "\n`acs/acs5` instead.\n" + '"""\n'

    def store_dataset(self, dataset_list: list, url_list: list):
        """
        Construct symbolic names and store as keys mapping to values of dataset and url.

        Parameters
        ----------
        dataset_list
            List of dataset names. Used to construct symbolic
            names and stored as value of symbolic name.

        url_list
            List of dataset urls. Stored as value of symbolic name.

        Returns
        -------
            A dictionary storing the symbolic names of unique data sets 
            that are available.
        """
        for item, link in zip(dataset_list, url_list):
            if item not in self.dictionary.values():
                temp = item.split("/")
                # Different cases of naming according to dataset names like 'acs/acs5' and special cases for clearer names
                if len(temp) == 1:
                    if temp[0][:3] == "ecn" or temp[0][:3] == "abs":
                        name = temp[0][:3].upper() + "_" + temp[0][3:].upper()
                    elif temp[0] == "surname":
                        name = "DECENNIAL_SURNAME"
                    elif temp[0] == "pubschlfin":
                        name = "PUBLIC_PK12_EDUCATION_FINANCE"
                    else:
                        name = temp[0].upper()
                elif len(temp) == 2:
                    if temp[0][:3] == temp[1][:3]:
                        if temp[0] == "popproj":
                            name = temp[0].upper()
                        else:
                            name = temp[1].upper()
                    else:
                        if temp[0] == "dec":
                            temp[0] = "decennial"
                            if temp[1] == "pl":
                                temp[1] = "PUBLIC_LAW_94_171"
                        name = "_".join(temp).upper()
                else:
                    if temp[0][:3] == temp[1][:3]:
                        name = "_".join(temp[1:]).upper()
                    else:
                        name = "_".join(temp[:2]).upper()
                item, link = f'"{item}"', f'"{link}"'
                self.dictionary[name] = [item, link]
        return self.dictionary

    def write_file(self, destination_file: str):
        """
        Write symbolic names dictionary content into destination file.

        Parameters
        ----------
        destination_file
            The target file for storing the datasets' symbolic names.
        """
        with open(destination_file, "w") as destfile:
            destfile.write(self.module_message)
            destfile.write("\n")

            for key in sorted(self.dictionary.keys()):
                destfile.write("\n")
                content = key + " = " + self.dictionary[key][0]
                destfile.write(content)
                destfile.write("\n")

            destfile.write("\n")
            destfile.write("\nDATASET_REFERENCE_URLS = { \n")

            for key in sorted(self.dictionary.keys()):
                value = self.dictionary[key][1]
                destfile.write("\t%s: %s,\n" % (key, value))
            destfile.write("}")

def main():
    df_datasets = ced.variables.all_data_sets()
    dataset_names = df_datasets["DATASET"].to_list()
    dataset_url = df_datasets["API BASE URL"].to_list()
    create_symbolic = symbolic()
    symbolic_names = create_symbolic.store_dataset(dataset_names, dataset_url)

    parser = argparse.ArgumentParser(description='Get destination file name.')
    parser.add_argument('filename', metavar='filename', type=str,
                        help='a file name for the symbolic name destination file')
    args = parser.parse_args()

    # path_directory = Path.cwd() #/censusdis
    path_directory = 'censusdis/'
    target_directory = Path(path_directory, args.filename)
    
    # censusdis_index = path_directory.parts.index("censusdis")
    # if censusdis_index == len(path_directory.parts)-1:
    #     target_directory = Path(path_directory, "censusdis", args.filename)
    # elif censusdis_index == len(path_directory.parts)-2 and path_directory.parts[-1] == "censusdis":
    #     target_directory = Path(path_directory, args.filename)
    # else:
    #     path_directory = path_directory.parents[len(path_directory.parts)-2-censusdis_index]
    #     target_directory = Path(path_directory, "censusdis", args.filename)
    create_symbolic.write_file(target_directory)
    print("Generated " + args.filename + " file successfully in " + str(target_directory))

if __name__ == "__main__":
    main()