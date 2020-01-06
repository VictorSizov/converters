import csv
import os
import sys

'''
headers = \
{ "accent_main":
 ('path',	'author',	'sex',	'birthday',	'header',	'created',	'sphere',	'genre_fi',	'type',	'topic',	'chronotop',	'style',
 'audience_age',	'audience_level',	'audience_size',	'subcorpus',	'date',-'ex',	'company',	'producer',	'company', 'pl',
 'not_place',	'source',	'tagging',),
  "spoken":
 ('path',	'header',	'source',	'source_small',	'author',	'sex',	'birthday',	'created',	'sphere',	'genre_fi',	'type',	'topic',
 'chronotop',	'style',	'audience_age',	'audience_level',	'audience_size',	'publisher',	'publ_year',	'medium',	'subcorpus',
 'not_place',	'source_hidden',	'tagging',),
  "manual":
  ('path',	'author',	'sex',	'birthday',	'header',	'created',	'sphere',	'genre_fi',	'type',	'topic',	'chronotop',	'style',
 'audience_age',	'audience_level',	'audience_size',	'source',	'publication',	'publisher',	'publ_year',	'medium',	'subcorpus',
 'tagging',		'comments',	'editor_id')
}
'''





def normalize_table(f_name):
    try:
        f_name = sys.argv[1]
        cp_name = f_name + '.bak'
        if os.path.exists(cp_name):
            print>>sys.stderr, "Error: backup file", cp_name, "exist"
            sys.exit(0)
        os.rename(f_name, cp_name)
        with open(cp_name, 'rb') as f_inp, open(f_name, 'wb') as f_out:
            reader = csv.DictReader(f_inp, delimiter=';', strict=True)
            writer = csv.DictWriter(f_out, reader.fieldnames, delimiter=';', lineterminator='\n', strict=True)
            writer.writeheader()
            for row in reader:
                path = row['path'].lower().replace('\\', '/')
                (path0, ext) = os.path.splitext(path)
                row['path'] = path0 if ext in ['.xml', '.xhtml'] else path
                writer.writerow(row)
    except (OSError, IOError) as e:
        print>>sys.stderr, "table ", f_name, "conversion error", e.message

if __name__ == '__main__':
    normalize_table(sys.argv[1])