"""table.py | Robin Forestier | 15.03.2022

This file contains the two class for create the two table in the settings page.
"""

# Importing the module `pickle` which allows saving and load python objects.
import pickle


# The Table class is a container for the data in a table
class Table:
    def __init__(self):
        """The function is used to initialize the class"""

        # The function is used to load the new_colonne_heure variable from the pickle file
        try:
            self.colonne_heure = self.get_colonne_heure()
            self.new_colonne_heure = self.get_new_colonne_heure()
            self.table = self.get_table()
        except FileNotFoundError:
            self.colonne_heure = []
            self.new_colonne_heure = []
            self.table = []

    def create(self):
        """This function is used to create the table if it doesn't exist"""
        self.colonne_heure = [("{:02d}:00".format(i)) for i in range(24)]
        self.table = [[0 for i in range(7)] for j in range(24)]

    def modif_table(self, row, column):
        """If the value of the cell is 3, change it to 0. Otherwise, add 1 to the value of the cell

        :param row: The row of the cell you want to change
        :type row: int
        :param column: The column of the cell you want to change
        :type column: int
        :return: The modified table.
        :rtype: list
        """

        if self.table[row][column] == 3:
            self.table[row][column] = 0
        else:
            self.table[row][column] += 1

        return self.table

    def add_custom_line(self, heure):
        """Add a new line to the table if it doesn't already exist

        :param heure: the time you want to add
        :type heure: str
        :return: The table and the list of the hours.
        :rtype: list
        """

        existing_heure = self.get_colonne_heure()

        if heure not in existing_heure:
            self.colonne_heure.append(heure)
            self.colonne_heure.sort()

            self.set_colonne_heure()

            self.new_colonne_heure.append(heure)
            self.new_colonne_heure.sort()

            self.set_new_colonne_heure()

            index = self.colonne_heure.index(heure)
            self.table.insert(index, [0 for i in range(7)])

            self.set_table()

        return self.table, self.colonne_heure

    def del_custom_line(self, heure):
        """It deletes the line of the table corresponding to the given heure

        :param heure: the hour you want to delete
        :type heure: str
        """
        index = self.new_colonne_heure.index(heure)
        self.new_colonne_heure.pop(index)

        index = self.colonne_heure.index(heure)
        self.colonne_heure.pop(index)

        self.table.pop(index)

        self.set_new_colonne_heure()
        self.set_colonne_heure()
        self.set_table()

    def set_table(self):
        """This function is used to save the table to a pickle file"""

        with open('./table/settings/table.pickle', 'wb') as f:
            pickle.dump(self.table, f, pickle.HIGHEST_PROTOCOL)

    def get_table(self):
        """It loads the table from the pickle file

        :return: The table
        :rtype: list
        """

        try:
            with open('./table/settings/table.pickle', 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self.table = pickle.load(f)

                return self.table
        except FileNotFoundError:
            self.create()
            self.set_table()
            self.set_colonne_heure()

            self.get_table()

    def set_colonne_heure(self):
        """The function is used to save the value of the variable "colonne_heure" in a file called "heure.pickle" """

        with open('./table/settings/heure.pickle', 'wb') as f:
            pickle.dump(self.colonne_heure, f, pickle.HIGHEST_PROTOCOL)

    def get_colonne_heure(self):
        """The function is used to load the value of the variable "colonne_heure" from a file called "heure.pickle

        :return: The list of the hours
        :rtype: list
        """
        try:
            with open('./table/settings/heure.pickle', 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self.colonne_heure = pickle.load(f)

                return self.colonne_heure
        except FileNotFoundError:
            self.create()
            self.set_table()
            self.set_colonne_heure()

            self.get_colonne_heure()

    def set_new_colonne_heure(self):
        """The function is used to save the new_colonne_heure variable in a pickle file"""

        with open('./table/settings/new_heure.pickle', 'wb') as f:
            pickle.dump(self.new_colonne_heure, f, pickle.HIGHEST_PROTOCOL)

    def get_new_colonne_heure(self):
        """The function is used to get the new_colonne_heure from the pickle file

        :return: The new_colonne_heure variable is being returned
        :rtype: list
        """

        try:
            with open('./table/settings/new_heure.pickle', 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self.new_colonne_heure = pickle.load(f)

                return self.new_colonne_heure
        except FileNotFoundError:
            self.set_new_colonne_heure()
            self.get_new_colonne_heure()


# It inherits from Table and overrides the __init__ method.
class Table2(Table):
    def __init__(self):
        """The __init__ function is called when an instance of the class is created.
        used to initialize the attributes of the class.
        """

        try:
            self.table = self.get_table()
            self.name = self.get_name()
        except FileNotFoundError:
            self.table = []
            self.name = []

    def create(self):
        """Create a table with 8 rows and 7 columns and create the name column."""

        self.table = [[0 for i in range(7)] for j in range(8)]
        self.name = ["Ligne 1", "Ligne 2", "Ligne 3", "Ligne 4", "Ligne 5", "Ligne 6", "Ligne 7", "couloir"]

    def modif_table(self, row, column):
        """Invert the value of a cell in the table

        :param row: The row of the cell you want to change
        :type row: int
        :param column: The column of the cell you want to change
        :type column: int
        :return: The modified table
        :rtype: list
        """

        if self.table[row][column] == 1:
            self.table[row][column] = 0
        else:
            self.table[row][column] = 1

        return self.table

    def set_table(self):
        """The function opens the pickle file and dumps the table into the pickle file"""

        with open('./table/settings/table2.pickle', 'wb') as f:
            pickle.dump(self.table, f, pickle.HIGHEST_PROTOCOL)

    def get_table(self):
        """Load the table from the pickle file

        :return: A table object
        :rtype: list
        """

        try:
            with open('./table/settings/table2.pickle', 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self.table = pickle.load(f)

                return self.table
        except FileNotFoundError:
            self.create()
            self.set_table()
            self.set_table()

            self.get_table()

    def set_name(self):
        """This function is used to set the name of the user"""

        with open('./table/settings/name.pickle', 'wb') as f:
            pickle.dump(self.name, f, pickle.HIGHEST_PROTOCOL)

    def get_name(self):
        """Get the name of the user

        :return: The name of the user
        :rtype: list
        """

        try:
            with open('./table/settings/name.pickle', 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self.name = pickle.load(f)

                return self.name
        except FileNotFoundError:
            self.create()
            self.set_table()
            self.set_name()

            self.get_colonne_heure()


if __name__ == '__main__':
    pass
