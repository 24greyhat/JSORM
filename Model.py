import json, os
from pathlib import Path
from typing import Any, Dict, List
import shutil



MAX_FIELD_PAGES = 10000 # max pages per subdir of a field
MAX_FIELD_PAGE_SIZE = 200000000 # max page size
# Note: a page is a json file that holds the values of a ModelField
# Pages are stored in subdirectories that are incrementally created upon reaching their upper limit
# Hopefully this allows this simple lib to provide some sort of scalibility and ease of use
# These are hyper parameters which you can ofc modify!


# Think of it like this: each field in your model is a book (e.g. dir) each book has chapters (e.g. subdirs) and each chapter has pages (e.g. json files containing list of values and type.__name__)


class ModelField:
    def __init__(self, field_type: type):
        self.field_type = field_type
        self.values = []



    def __repr__(self):
        return json.dumps({
            "values": self.values,
            "type": self.field_type.__name__
        })




class Model:
    def __init__(self):
        self.name = self.__class__.__name__
        self.fields = []

        self.root = Path(".jsorm")

        self.dbpath = self.root / "models"


        if not self.root.exists():
            self.root.mkdir()


        if not self.dbpath.exists():
            self.dbpath.mkdir()


        dbpath = self.dbpath / self.name

        if not dbpath.exists():
            dbpath.mkdir()

        self.__loadFields__()



    def __loadFields__(self):
        self.fields = []
        for key, value in list(zip(self.__class__.__dict__.keys(), self.__class__.__dict__.values())):

            if type(value) == ModelField:
                self.fields.append({"name": key, "data": json.loads(value.__repr__())})

                fp = self.dbpath / self.name / f'{key}'

                if not fp.exists():
                    fp.mkdir()


                    fp = fp / "0" 

                    if not fp.exists():
                        fp.mkdir()


                    fp = fp / "0.json"

                    with open(fp, "w") as f:
                        f.write(value.__repr__())



    # returns the last free 
    def __getFieldFreePath__(self, name) -> Path | None:

        global MAX_FIELD_FILES, MAX_FIELD_FILE_SIZE

        db = self.dbpath / self.name / name
        subdirs = os.listdir(db)

        try:

            lastsub = subdirs.pop() # gets last subdir

            p = db / lastsub

            files = os.listdir(p)

            lastfile = files.pop() # get the last page in the subdir

            if os.path.getsize(p / lastfile) < MAX_FIELD_PAGE_SIZE: # if last page is not maxed out then return it
                return p / lastfile

            if len(files)+1 >= MAX_FIELD_PAGES: # if the subdir is maxed out and there is not free last file then create new subdir
                p = db / str(int(lastsub)+1)
                if not p.exists():
                    p.mkdir()


            p = p / f"{len(files)}.json" # create a new page (in new subdir or last free subdir)

            if not p.exists():
                p.touch()

            return p # return new file

        except Exception:
            return None


    # loads all the current values of the field from the last free field file
    def __loadFieldValues__(self, name: str) -> None:
        fp = self.__getFieldFreePath__(name)

        try:
            if fp:
                with open(fp, "r") as f:
                    content = json.loads(f.read())

                    for f in self.fields:
                        if f['name'] == name:
                            i = self.fields.index(f)
                            self.fields[i]['data']['values'] = content['data']['values']
                            self.fields[i]['data']['type'] = content['data']['type']
                            return
        except Exception:
            return None
        


    # new record: field_name=field_value, ...
    def create(self, **args) -> None | Exception:
        self.__loadFields__()

        try:
            for field_name, field_value in zip(args.keys(), args.values()):
                for field in self.fields:
                    if field['name'] == field_name:
                        i = self.fields.index(field)
                        f = self.fields[i]['data']

                        if f['type'] == type(field_value).__name__:
                            self.__loadFieldValues__(field_name)
                            self.fields[i]['data']['values'].append(field_value)

                            fp = self.__getFieldFreePath__(field_name)
                            
                            if fp:
                                with open(fp, "w") as f:
                                    f.write(json.dumps(self.fields[i]))

                        else:
                            raise TypeError(f'Can not store value of type "{type(field_value).__name__}" in field of type "{f['type']}" ({field_name})')
        except Exception as e:
                return e


    def __getFieldPages__(self, name: str) -> List[Path] | None:
        try:
            self.__loadFields__()
            p = self.dbpath / self.name / name

            subdirs = os.listdir(p)

            pages = []

            for sub in subdirs:
                x = p / sub

                pgs = os.listdir(x)

                for page in pgs:
                    pages.append(x / page)

            return pages

        except Exception:
            return None




    # get all the values of the field
    def values(self, name: str, limit: int = 100) -> List[Dict] | None:
        try:
            pages = self.__getFieldPages__(name)

            if not pages:
                return None


            idx = len(pages)


            results = []


            while idx > 0:
                page = pages[idx-1]

                with open(page, "r") as f:
                    content = json.loads(f.read())

                    values = content['data']['values']

                    if len(values) >= limit:
                        return values[0:limit]

                    else:
                        for i in values:
                            if len(results) < limit:
                                results.append(i)

                            else:
                                return results
                idx-=1

            return results
        except KeyboardInterrupt:
            return None


    # search field
    def search(self, name: str, search_query: str, limit: int = 100) -> List[Dict] | None:
        try:
            pages = self.__getFieldPages__(name)

            if not pages:
                return None


            results = []

            idx = len(pages)


            results = []


            while idx > 0:
                page = pages[idx-1]

                with open(page, "r") as f:
                    content = json.loads(f.read())

                    values = content['data']['values']

                    for i in values:
                        if str(i).find(search_query) != -1:
                            if len(results) < limit:
                                results.append(i)

                            else:
                                return results
                idx-=1

            return results
        except Exception:
            return None



    def update(self, name: str, value: Any, new_value: Any) -> Any | None:
        try:
            pages = self.__getFieldPages__(name)

            if not pages:
                return None


            idx = len(pages)


            while idx > 0:
                page = pages[idx-1]

                with open(page, "r") as f:
                    content = json.loads(f.read())

                    values = content['data']['values']

                    for i in values:
                        if value == i:
                            idx = values.index(i)
                            values[idx] = new_value

                            f.close()

                            with open(page, "w") as fp:
                                fp.write(json.dumps(content))
                                return new_value
                idx-=1
        except Exception:
            return None




    def delete(self, name: str, value: Any) -> Any | None:
        try:
            pages = self.__getFieldPages__(name)

            if not pages:
                return None


            idx = len(pages)



            while idx > 0:
                page = pages[idx-1]

                with open(page, "r") as f:
                    content = json.loads(f.read())

                    values = content['data']['values']

                    for i in values:
                        if value == i:
                            values.remove(i)

                            f.close()

                            with open(page, "w") as fp:
                                fp.write(json.dumps(content))
                idx-=1
        except Exception:
            return None


    def getRows(self, limit: int = 100) -> dict:
        try:
            results = dict()

            for field in self.fields:
                results.update({field['name']: self.values(field['name'], limit)})

            return results
        except Exception:
            return {}


    # get row where field_name = field_value
    def getRow(self, field_name: str, field_value):
        try:
            pages = self.__getFieldPages__(field_name)

            if not pages:
                return None


            row = dict()

            idx = len(pages)


            pageIndex = None

            rowIndex = 0

            while idx > 0:
                page = pages[idx-1]

                with open(page, "r") as f:
                    content = json.loads(f.read())

                    values = content['data']['values']

                    rowIndex = -1
                    for i in values:
                        if field_value == i:
                            row.update({field_name: i})
                            rowIndex+=1
                            break

                idx-=1

            pageIndex = idx-1


            for field in self.fields:
                fpages = self.__getFieldPages__(field['name'])

                if not fpages or not len(fpages):
                    continue

                if field['name'] != field_name:

                     with open(fpages[pageIndex], "r") as f:
                        content = json.loads(f.read())

                        values = content['data']['values']

                        if len(values) >= rowIndex+1:
                            row.update({field['name']: values[rowIndex]})

                        else:
                            row.update({field['name']: None})

            return row
            
        except Exception:
            return None






    # creates a zipFile of the model and saves it to save_path to be transfered etc...
    # returns path where the model is saved or None if an exception occurs
    def exportModelZipFile(self, save_path: str = ".") -> None | Exception:
        try:
            self.__loadFields__()


            path = self.dbpath / self.name

            shutil.make_archive(f"{save_path}/{self.name}", "zip", path)

        except Exception as e:
            return e




