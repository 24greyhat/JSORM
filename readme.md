### JSORM

> A simple json orm in python

<hr/>


#### 1) Example:

```python

from Model import Model, ModelField



class Person(Model):
    id = ModelField(int)
    name = ModelField(str)
    age = ModelField(int)
    rank = ModelField(float)



instance = Person()

instance.create(id=1, name="John Doe", age=20, rank=2.59)

results1 = instance.search("id", "1", limit=1)


results2 = instance.values("id", limit=100)


instance.update(name="id", value=1, new_value=2)


results3 = instance.values("id")


instance.exportModelZipFile(".")
```




### Example Retrieving entire row:

```python


class RowExample(Model):
    x = ModelField(int)
    y = ModelField(int)



w = RowExample()

w.create(x=10, y=20)
w.create(x=20, y=None)

print(w.getRow("x", 10)) # {'x': 10, 'y': 20}
print(w.getRow("x", 20)) # {'x': 10, 'y': None}


```
