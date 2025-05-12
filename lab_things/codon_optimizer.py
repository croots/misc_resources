'''
Two core scripts for generating codon-optimized sequences.

hard_optimize(): Replaces codons in a sequence with the most common codon for your desired organism
weighted_optimize(): Uses weighted randomization to generate a codon optimized sequence that still takes advantage of all codons
                     with at least user defined frequency
                     
Both functions take protein sequences, not nucleotide, and a codon table in a folder named 'codontables' in the same root directory as
the script. You can find some examples in this repo.

Requires NUMPY

@author: croots
@version: 0.1

'''

from numpy.random import choice
from warnings import warn
from pkg_resources import resource_filename
from os import listdir, path
import json
from itertools import product, chain


def available_tables(info="all") -> list:  # Should be easy to follow
    '''Returns list of available codontables as [organism, type, name_for_use]'''
    table_loc = resource_filename(__name__, 'codontables')
    tables = listdir(table_loc)
    table_list = []
    for table in tables:
        with open(table_loc + "/" + table) as f:
            table_contents = json.load(f)
        if info == "all":
            table_info = [table_contents["meta"]["name"],
                          table_contents["meta"]["type"],
                          path.splitext(table)[0]]
        elif info == "usage_name":
            table_info = path.splitext(table)[0]
        else:
            raise ValueError(f"Table info type '{info} unrecognized")
        table_list.append(table_info)
    return table_list


def _table_prep(table):
    """Takes user input table and ensures it's valid for future use."""
    codon_tables = available_tables(info="usage_name")
    if type(table) == dict:  # Allows user to set a manual table
        pass
    elif table in codon_tables:  # Grabs a predefined table otherwise
        table_loc = resource_filename(__name__, 'codontables')
        with open(table_loc + "/" + table + ".json") as f:
            table_contents = json.load(f)
        table = table_contents["table"]
    else:
        raise ValueError("Could not phrase supplied codon table.")
    all_codons = ["".join(x) for x in [codon for codon in product("ATCG", repeat=3)]]
    print(all_codons)
    codons_present = list(chain(*[list(table[aa].keys()) for aa in table]))
    codons_missing = [codon for codon in all_codons if codon not in codons_present]  # Find missing codons
    if codons_missing:  # Report them to the user
        warn(f"The following codons were not found in supplied table: {', '.join(codons_missing)}.")
    duplicate_codons = set([codon for codon in codons_present if codons_present.count(codon) > 1])  # Find dupe codons
    if duplicate_codons:  # Report them to the user
        warn(f"The following codons appear more than once in the supplied table: {', '.join(duplicate_codons)}.")
    return table


def weighted_optimize(protein, table, avoid_less_than=.15) -> str:
    """Optimizes string of amino acids 'protein' for organism 'table' by weight of codon frequency."""
    table = _table_prep(table)
    result = str()  # Defines resulting nucleotide string variable
    for i, aa in enumerate(protein):  # Selects nucleotide for every amino acid
        if i+1 < len(protein) and aa == "*":
            warn(f"Your protein may have a premature stop at position {i+1} (indexed to 1).")
        aa = aa.upper()
        codon_table = table[aa]
        for key, value in codon_table.items():  # Removes codons of user-defined rarity from the pool
            if value < avoid_less_than:
                codon_table[key] = 0
        elements = list(codon_table.keys())
        weights = list(codon_table.values())
        weight_sum = sum(weights)
        if weight_sum == 0:
            raise ValueError(f"No usable codons found for {aa}. Consider reducing 'avoid_less_than'.")
        elif weight_sum < 1:  # Balances codon frequency to total 1 if too low, esp. after removing rare ones
            weight_delta = 1-weight_sum
            elements = elements + [""]
            weights = weights + [weight_delta]
        elif weight_sum > 1:
            raise ValueError(f"Total codon weight for {aa} is greater than 1")
        codon = ""
        while not codon:  # Actually does the picking
            codon = choice(elements, p=weights)
        result = result + codon  # Builds nucleotide string
    return result


def hard_optimize(protein, table) -> str:
    """Optimizes string of amino acids 'protein' for organism 'table' by most frequent codon."""
    table = _table_prep(table)
    result = str()
    for i, aa in enumerate(protein):  # Selects nucleotide for every amino acid
        if i+1 < len(protein) and aa == "*":
            warn(f"Your protein may have a premature stop at position {i+1} (indexed to 1).")
        aa = aa.upper()
        codon = max(table[aa], key=table[aa].get)
        result = result + codon  # Builds nucleotide string
    return result


if __name__ == "__main__":
    print(weighted_optimize("SAARLL",
                            "drosophila",
                            avoid_less_than=0.05))
