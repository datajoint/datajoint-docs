# Principles

The DataJoint framework provides a systematic approach for managing scientific data and computation. 
DataJoint is a new clarification of the classical 
[relational model](https://en.wikipedia.org/wiki/Relational_model).
Most notably, DataJoint extends the data model to introduce the concept of 
*computational dependencies* as its native citizen. 
These modifications of the relational data model simplify its use for organizing scientific data. 

## Data definition 

### Data representation

1. All data are represented in the form of *entity sets*, i.e. an ordered collection of *entities* belonging to one *entity class*. 
3. All entities in a given entity set have the same set of named attributes. 
4. Each entity set has a *primary key*, *i.e.* a subset of attributes that, jointly, uniquely identify 
5. Each attribute in an entity set has a *data type* (or *domain*), representing a set of valid values.
6. Each Entity provides *attribute values* for all of the attributes of its entity sets.

We often use simpler (while less precise) terms:

* entity set = *table* 
* attribute = *column*
* attribute value = *field*

DataJoint introduces a streamlined syntax for defining an entity set. 
Each line of the definition defines an attribute with its name, data type, an optional default value, and an optional comment in the format:
```
name [=value] : type  [# comment]
```

Primary attributes come first and are separated from the rest of the attributes with the divider `---`.

For example, the following code defines the entity set for entities of class `Employee`:

```
employee_id : int
---
ssn = null : int     # optional social security number
date_of_birth : date
gender : enum('male', 'female', 'other')
home_address="" : varchar(1000) 
primary_phone="" : varchar(12)
```

Entity sets (tables) can be *stored* or *derived*. 

### Data normalization 
A collection of data are considered normalized when they are organized into a collection of entity sets, 
where each entity set contains entities of the same class and where all attributes apply to each entity 
and where the same primary key can identify all entities. 

The normalization procedure often includes splitting data from one table into several tables, 
one for each proper entity set. 

### Entity integrity
*Entity integrity* is the guarantee made by the data management process of the 1:1 mapping between 
real-world entities and their digital representations. 
In practice, entity integrity is ensured when it is made clear 

### Databases and Schemas 
Stored tables have names grouped into namespaces called *schemas* within *databases*. 
A *database* is a globally unique address or name. A *schema* is a unique name within a database. 
Within a *connection* to a particular database, a stored table is identified 
A schema typically groups tables that are logically related.


### Dependencies 
Entity sets can form referential dependencies that express and 


### Diagramming 

## Data manipulations

## Data queries 

### Operators 

## Computational dependencies 

