import unittest
from typing import Any, Dict, Iterable, List, Optional

from censusdis.impl.varcache import VariableCache
from censusdis.impl.varsource.base import VariableSource


class VariableCacheTestCase(unittest.TestCase):
    class MockVariableSource(VariableSource):
        """A mock variable source."""

        def __init__(self):
            self._gets = 0
            self._group_gets = 0
            self._all_group_gets = 0

        @property
        def gets(self):
            return self._gets

        @property
        def group_gets(self):
            return self._group_gets

        @property
        def all_group_gets(self):
            return self._all_group_gets

        def reset_counts(self):
            self._gets = 0
            self._group_gets = 0
            self._all_group_gets = 0

        def get(self, source: str, year: int, name: str) -> Dict[str, Any]:
            """
            Construct a mock variable.

            This looks a bit like a variable we get get from
            https://api.census.gov/data/2020/acs/acs5/variables/B03002_001E.json
            """
            self._gets = self.gets + 1

            return {
                "name": f"{name}",
                "label": "Estimate!!Total:",
                "concept": "HISPANIC OR LATINO ORIGIN BY RACE",
                "predicateType": "int",
                "group": name.split("_")[0],
                "limit": 0,
                "attributes": f"{name}A,{name}M,{name}MA",
            }

        def get_group(self, source: str, year: int, group_name: str) -> Dict[str, Dict]:
            """
            Construct a mock group.

            This looks a bit like a subset of what we might get from
            https://api.census.gov/data/2020/acs/acs5/groups/B03002.json
            """
            self._group_gets = self.group_gets + 1

            return {
                "variables": {
                    f"{group_name}_002E": {
                        "name": f"{group_name}_002E",
                        "label": "Estimate!!Total:!!Not Hispanic or Latino:",
                        "concept": "HISPANIC OR LATINO ORIGIN BY RACE",
                        "predicateType": "int",
                        "group": f"{group_name}",
                        "limit": 0,
                        "predicateOnly": True,
                        "universe": "TOTAL_POP",
                    },
                    f"{group_name}_003E": {
                        "name": f"{group_name}_003E",
                        "label": "Estimate!!Total:!!Not Hispanic or Latino:!!White alone",
                        "concept": "HISPANIC OR LATINO ORIGIN BY RACE",
                        "predicateType": "int",
                        "group": f"{group_name}",
                        "limit": 0,
                        "predicateOnly": True,
                        "universe": "TOTAL_POP",
                    },
                    f"{group_name}_004E": {
                        "name": f"{group_name}_004E",
                        "label": "Estimate!!Total:!!Not Hispanic or Latino:!!Black or African American alone",
                        "concept": "HISPANIC OR LATINO ORIGIN BY RACE",
                        "predicateType": "int",
                        "group": f"{group_name}",
                        "limit": 0,
                        "predicateOnly": True,
                        "universe": "TOTAL_POP",
                    },
                }
            }

        def get_all_groups(self, dataset: str, year: int) -> Dict[str, List]:
            """
            Construct a collection (of size 1) of groups.

            This looks a bit like a subset of what we might get from
            https://api.census.gov/data/2020/acs/acs5/groups.json
            """
            self._all_group_gets = self.all_group_gets + 1

            return {
                "groups": [
                    {
                        "name": "B03001",
                        "description": "HISPANIC OR LATINO ORIGIN BY SPECIFIC ORIGIN",
                        "variables": "http://api.census.gov/data/2020/acs/acs5/groups/B03001.json",
                        "universe ": "TOTAL_POP",
                    },
                    {
                        "name": "B25031",
                        "description": "MEDIAN GROSS RENT BY BEDROOMS",
                        "variables": "http://api.census.gov/data/2020/acs/acs5/groups/B25031.json",
                        "universe ": "RENTER_OCCUPIED_UNIT_CASH",
                    },
                ]
            }

        def get_datasets(self, year: Optional[int]) -> Dict[str, Any]:
            return {
                "dataset": [
                    {
                        "c_vintage": 2019 if year is None else year,
                        "c_dataset": ["acs", "acs5"],
                        "title": "American Community Survey: 5-Year Estimates: Data Tables",
                        "description": "Description of the dataset...",
                    }
                ]
            }

        def group_variable_names(
            self, source: str, year: int, group_name: str
        ) -> Iterable[str]:
            variables = self.get_group(source, year, group_name)["variables"]
            for variable in variables.values():
                yield variable["name"]

    def setUp(self) -> None:
        """Set up before each test."""
        self.source = "acs/acs5"
        self.year = 2020
        self.mock_source = self.MockVariableSource()
        self.variables = VariableCache(variable_source=self.mock_source)

    def test_operators(self):
        """Test basic operators."""
        self.assertEqual(0, len(self.variables))
        self.assertNotIn((self.source, self.year, "X02002_002E"), self.variables)

        self.assertEqual(0, self.mock_source.gets)
        self.assertEqual(0, self.mock_source.group_gets)

        _ = self.variables[self.source, self.year, "X02002_002E"]
        self.assertEqual(1, len(self.variables))
        self.assertIn((self.source, self.year, "X02002_002E"), self.variables)

        self.assertEqual(1, self.mock_source.gets)
        self.assertEqual(0, self.mock_source.group_gets)

        # No second call to the source if we hit in the cache.
        _ = self.variables[self.source, self.year, "X02002_002E"]

        self.assertEqual(1, self.mock_source.gets)
        self.assertEqual(0, self.mock_source.group_gets)

    def test_get(self):
        self.assertEqual(0, len(self.variables))
        variable = self.variables.get(self.source, self.year, "X01001_001E")

        # One in the cache now.
        self.assertEqual(1, len(self.variables))
        self.assertIn((self.source, self.year, "X01001_001E"), self.variables)

        self.assertEqual("X01001_001E", variable["name"])
        self.assertEqual("X01001", variable["group"])
        self.assertEqual("Estimate!!Total:", variable["label"])

        self.variables.invalidate(self.source, self.year, "X01001_001E")

        # No longer in the cache.
        self.assertEqual(0, len(self.variables))
        self.assertNotIn((self.source, self.year, "X01001_001E"), self.variables)

    def test_many_vars(self):
        for n, source in enumerate(["foo/abc", "bar/xyz"]):
            for ii in range(20):
                name = f"X01001_0{ii:02}E"

                source_variable = self.mock_source.get(source, self.year, name)
                cached_variable = self.variables.get(source, self.year, name)

                self.assertEqual(40 * n + 2 * ii + 2, self.mock_source.gets)
                self.assertEqual(0, self.mock_source.group_gets)

                self.assertEqual(20 * n + ii + 1, len(self.variables))
                self.assertIn((source, self.year, name), self.variables)
                self.assertEqual(source_variable, cached_variable)

                # These all hit in the cache, so the get count does not go up.
                self.variables.get(source, self.year, name)
                _ = self.variables[source, self.year, name]
                self.variables.get(source, self.year, name)
                _ = self.variables[source, self.year, name]

                self.assertEqual(40 * n + 2 * ii + 2, self.mock_source.gets)
                self.assertEqual(0, self.mock_source.group_gets)

        # Now drop half of them, just from the last source.
        for ii in range(20):
            name = f"X01001_0{ii:02}E"
            self.variables.invalidate(source, self.year, name)
            self.assertEqual(20 * (n + 1) - (ii + 1), len(self.variables))

        # Bulk drop the rest
        self.variables.clear()
        self.assertEqual(0, len(self.variables))

    def test_group(self):
        self.assertEqual(0, self.mock_source.gets)
        self.assertEqual(0, self.mock_source.group_gets)

        group = self.variables.get_group(self.source, self.year, "X02002")
        self.assertEqual(3, len(group))

        # We only make the one group call to the source, not
        # calls for all the individual variables.
        self.assertEqual(0, self.mock_source.gets)
        self.assertEqual(1, self.mock_source.group_gets)

        # All the variables in the group should now be in the cache.
        self.assertEqual(3, len(self.variables))

        for name in group.keys():
            self.assertIn((self.source, self.year, name), self.variables)
            self.assertEqual(
                "X02002", self.variables[self.source, self.year, name]["group"]
            )
            self.assertEqual(name, self.variables[self.source, self.year, name]["name"])

        # We had all the variables in the cache.
        self.assertEqual(0, self.mock_source.gets)

    def test_group_leaves(self):
        leaves = self.variables.group_leaves(self.source, self.year, "X02002")

        self.assertEqual(["X02002_003E", "X02002_004E"], leaves)

    def test_group_tree(self):
        tree = self.variables.group_tree(self.source, self.year, "X02002")

        self.assertEqual(
            """+ Estimate
    + Total:
        + Not Hispanic or Latino: (X02002_002E)
            + White alone (X02002_003E)
            + Black or African American alone (X02002_004E)""",
            str(tree),
        )

        self.assertEqual(1, len(tree))
        self.assertFalse(tree.is_leaf())

        t1 = tree["Estimate"]
        self.assertIsNone(t1.name)
        self.assertEqual(1, len(t1))
        self.assertFalse(t1.is_leaf())

        t11 = t1["Total:"]
        self.assertIsNone(t11.name)
        self.assertEqual(1, len(t11))
        self.assertFalse(t11.is_leaf())

        t111 = t11["Not Hispanic or Latino:"]
        self.assertEqual("X02002_002E", t111.name)
        self.assertEqual(2, len(t111))
        self.assertFalse(t111.is_leaf())

        t1111 = t111["White alone"]
        self.assertEqual("X02002_003E", t1111.name)
        self.assertEqual(0, len(t1111))
        self.assertTrue(t1111.is_leaf())

        t1112 = t111["Black or African American alone"]
        self.assertEqual("X02002_004E", t1112.name)
        self.assertEqual(0, len(t1112))
        self.assertTrue(t1112.is_leaf())

        leaves = list(tree.leaves())
        self.assertEqual(2, len(leaves))
        leaf_names = [leaf.name for leaf in leaves]
        self.assertIn("X02002_003E", leaf_names)
        self.assertIn("X02002_004E", leaf_names)

    def test_variables_iterables(self):
        # Initially, there are no variables cached locally.
        keys = frozenset(self.variables.keys())
        values = list(self.variables.values())
        items = list(self.variables.items())
        self.assertEqual(0, len(keys))
        self.assertEqual(0, len(values))
        self.assertEqual(0, len(items))

        # After we load a group, the variables in the group
        # are in the cache.
        group_name = "X02002"

        tree = self.variables.group_tree(self.source, self.year, group_name)

        # Check that all the dict-like iterables work.
        keys = frozenset(self.variables.keys())
        values = list(self.variables.values())
        items = list(self.variables.items())

        mock_variable_names = list(
            self.mock_source.group_variable_names(self.source, self.year, group_name)
        )

        # We should have one variable for each mock variable name.
        self.assertEqual(len(mock_variable_names), len(keys))

        for mock_variable_name in mock_variable_names:
            self.assertIn((self.source, self.year, mock_variable_name), keys)

        # We should have a value for each variable name.
        self.assertEqual(len(mock_variable_names), len(values))

        # The items should contain what the keys and values contain.
        self.assertEqual(len(keys), len(items))
        self.assertEqual(len(values), len(items))

        for item in items:
            self.assertIn(item[0], keys)
            self.assertIn(item[1], values)

        # Now look in the root node, which is just for
        # estimates. The mock paths look like
        # "Estimate!!Total!!Description" so we should
        # be able to find them.
        for estimate_name, estimate_node in tree.items():
            self.assertEqual("Estimate", estimate_name)

            # From the root, we will iterate down through the levels
            # we mocked out down to the leaves.
            for total_name, total_node in estimate_node.items():
                self.assertEqual("Total:", total_name)
                self.assertFalse(total_node.is_leaf())

                for ethnicity_name, ethnicity_node in total_node.items():
                    self.assertEqual("Not Hispanic or Latino:", ethnicity_name)
                    self.assertFalse(ethnicity_node.is_leaf())

                    leaf_names = frozenset(ethnicity_node.keys())

                    self.assertEqual(2, len(leaf_names))
                    self.assertIn("White alone", leaf_names)
                    self.assertIn("Black or African American alone", leaf_names)

                    for leaf_node in ethnicity_node.values():
                        self.assertTrue(leaf_node.is_leaf())

    def test_all_datasets(self):
        """
        Test :py:meth:`~censisdis.impl.varcache.VariableCache.all_data_sets`.

        Do it twice to cover the cached and uncached code paths.
        """
        df_datasets_first_time = self.variables.all_data_sets()

        self.assertEqual((1, 5), df_datasets_first_time.shape)

        df_datasets_cached = self.variables.all_data_sets()

        df_datasets_first_time = df_datasets_first_time.replace([None], "-")

        df_datasets_cached = df_datasets_cached.replace([None], "-")

        self.assertTrue((df_datasets_first_time == df_datasets_cached).all().all())

        self.assertEqual(
            ["YEAR", "DATASET", "TITLE", "DESCRIPTION", "API BASE URL"],
            list(df_datasets_cached.columns),
        )

    def test_all_groups(self):
        """
        Test :py:meth:`~censisdis.impl.varcache.VariableCache.all_groups`.

        Do it twice to cover the cached and uncached code paths.
        """
        df_datasets = self.variables.all_data_sets()

        dataset = df_datasets.iloc[0]["DATASET"]
        year = df_datasets.iloc[0]["YEAR"]

        df_groups_first_time = self.variables.all_groups(dataset, year)
        self.assertEqual((2, 4), df_groups_first_time.shape)

        df_groups_cached = self.variables.all_groups(dataset, year)

        self.assertTrue((df_groups_first_time == df_groups_cached).all().all())

    def test_all_variables(self):
        """
        Test :py:meth:`~censisdis.impl.varcache.VariableCache.all_variables`.

        Do it twice to cover the cached and uncached code paths.
        """
        df_datasets = self.variables.all_data_sets()

        dataset = df_datasets.iloc[0]["DATASET"]
        year = df_datasets.iloc[0]["YEAR"]

        df_groups = self.variables.all_groups(dataset, year)

        group = df_groups.iloc[0]["GROUP"]

        df_variables_first_time = self.variables.all_variables(dataset, year, group)

        self.assertEqual((3, 7), df_variables_first_time.shape)

        df_variables_cached = self.variables.all_variables(dataset, year, group)

        # The last two columns are null, so they don't compare as equal. But make
        # sure both are or they are equal, but not both.
        df_equal_or_both_null = (df_variables_first_time == df_variables_cached) ^ (
            df_variables_cached.isnull() & df_variables_cached.isnull()
        )

        self.assertTrue(df_equal_or_both_null.all().all())


if __name__ == "__main__":
    unittest.main()
