---
title: Example Schema
---

The example schema below contains data for a university enrollment
system. Information about students, departments, courses, etc. are
organized in multiple tables.

=== "Python"

  <div class="warning">

  <div class="title">

  Warning

  </div>

  Empty primary keys, such as in the `CurrentTerm` table, are not yet
  supported by DataJoint. This feature will become available in a future
  release. See [Issue
  \#113](https://github.com/datajoint/datajoint-python/issues/113) for
  more information.

  </div>

  ``` python
  @schema
  class Student (dj.Manual):
    definition = """
    student_id      : int unsigned # university ID
    ---
    first_name      : varchar(40)
    last_name       : varchar(40)
    sex             : enum('F', 'M', 'U')
    date_of_birth   : date
    home_address    : varchar(200) # street address
    home_city       : varchar(30)
    home_state      : char(2) # two-letter abbreviation
    home_zipcode    : char(10)
    home_phone      : varchar(14)
    """

  @schema
  class Department (dj.Manual):
    definition = """
    dept         : char(6) # abbreviated department name, e.g. BIOL
    ---
    dept_name    : varchar(200) # full department name
    dept_address : varchar(200) # mailing address
    dept_phone   : varchar(14)
    """

  @schema
  class StudentMajor (dj.Manual):
    definition = """
    -> Student
    ---
    -> Department
    declare_date :  date # when student declared her major
    """

  @schema
  class Course (dj.Manual):
    definition = """
    -> Department
    course      : int unsigned # course number, e.g. 1010
    ---
    course_name : varchar(200) # e.g. "Cell Biology"
    credits     : decimal(3,1) # number of credits earned by completing the course
    """

  @schema
  class Term (dj.Manual):
    definition = """
    term_year : year
    term      : enum('Spring', 'Summer', 'Fall')
    """

  @schema
  class Section (dj.Manual):
    definition = """
    -> Course
    -> Term
    section : char(1)
    ---
    room  :  varchar(12) # building and room code
    """

  @schema
  class CurrentTerm (dj.Manual):
    definition = """
    ---
    -> Term
    """

  @schema
  class Enroll (dj.Manual):
    definition = """
    -> Section
    -> Student
    """

  @schema
  class LetterGrade (dj.Manual):
    definition = """
    grade : char(2)
    ---
    points : decimal(3,2)
    """

  @schema
  class Grade (dj.Manual):
    definition = """
    -> Enroll
    ---
    -> LetterGrade
    """
  ```

=== "Matlab"

  <div class="warning">

  <div class="title">

  Warning

  </div>

  Empty primary keys, such as in the `CurrentTerm` table, are not yet
  supported by DataJoint. This feature will become available in a future
  release. See [Issue
  \#127](https://github.com/datajoint/datajoint-matlab/issues/127) for
  more information.

  </div>

  File `+university/Student.m`

  ``` matlab
  %{
    student_id      : int unsigned # university ID
    ---
    first_name      : varchar(40)
    last_name       : varchar(40)
    sex             : enum('F', 'M', 'U')
    date_of_birth   : date
    home_address    : varchar(200) # street address
    home_city       : varchar(30)
    home_state      : char(2) # two-letter abbreviation
    home_zipcode    : char(10)
    home_phone      : varchar(14)
  %}
  classdef Student < dj.Manual
  end
  ```

  File `+university/Department.m`

  ``` matlab
  %{
    dept         : char(6) # abbreviated department name, e.g. BIOL
    ---
    dept_name    : varchar(200) # full department name
    dept_address : varchar(200) # mailing address
    dept_phone   : varchar(14)
  %}
  classdef Department < dj.Manual
  end
  ```

  File `+university/StudentMajor.m`

  ``` matlab
  %{
    -> university.Student
    ---
    -> university.Department
    declare_date :  date # when student declared her major
  %}
  classdef StudentMajor < dj.Manual
  end
  ```

  File `+university/Course.m`

  ``` matlab
  %{
    -> university.Department
    course      : int unsigned # course number, e.g. 1010
    ---
    course_name : varchar(200) # e.g. "Cell Biology"
    credits     : decimal(3,1) # number of credits earned by completing the course
  %}
  classdef Course < dj.Manual
  end
  ```

  File `+university/Term.m`

  ``` matlab
  %{
    term_year : year
    term      : enum('Spring', 'Summer', 'Fall')
  %}
  classdef Term < dj.Manual
  end
  ```

  File `+university/Section.m`

  ``` matlab
  %{
    -> university.Course
    -> university.Term
    section : char(1)
    ---
    room  :  varchar(12) # building and room code
  %}
  classdef Section < dj.Manual
  end
  ```

  File `+university/CurrentTerm.m`

  ``` matlab
  %{
    ---
    -> university.Term
  %}
  classdef CurrentTerm < dj.Manual
  end
  ```

  File `+university/Enroll.m`

  ``` matlab
  %{
    -> university.Section
    -> university.Student
  %}
  classdef Enroll < dj.Manual
  end
  ```

  File `+university/LetterGrade.m`

  ``` matlab
  %{
    grade : char(2)
    ---
    points : decimal(3,2)
  %}
  classdef LetterGrade < dj.Manual
  end
  ```

  File `+university/Grade.m`

  ``` matlab
  %{
    -> university.Enroll
    ---
    -> university.LetterGrade
  %}
  classdef Grade < dj.Manual
  end
  ```

# Example schema ERD

<figure>
<img src="../_static/img/queries_example_erd.png" class="align-center"
alt="Example schema for a university database. Tables contain data on students, departments, courses, etc." />
<figcaption aria-hidden="true">Example schema for a university database.
Tables contain data on students, departments, courses, etc.</figcaption>
</figure>
