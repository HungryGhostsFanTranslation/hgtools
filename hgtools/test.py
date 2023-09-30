from parsers import hgpack

p=hgpack.Hgpack.from_file("/Users/cschmidt/PycharmProjects/hungry_ghosts/extracted/data/pack.dat")

directories = p.directories

for d in directories:
  if d.directory_index.unkn_d !=0:
    print(d.directory_index.unkn_i)
    print(d.directory_index.id)
