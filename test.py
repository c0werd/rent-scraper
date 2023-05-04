from tabulate import tabulate

alist = [["Sun",696000,1989100000],["Earth",6371,5973.6], ["Moon",1737,73.5],["Mars",3390,641.85]]\

topgn = "```" + tabulate(alist, headers='keys',tablefmt='pipe',numalign='left',stralign='center') + "```"
print(topgn)