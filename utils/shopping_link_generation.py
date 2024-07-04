import urllib.parse
import os

class ShoppingLinkGenerator:
    """
    A class to generate shopping links for ingredients from Amazon and Blinkit.

    This class provides methods to generate affiliate links for Amazon and search links for Blinkit.
    
    Attributes
    ----------
    amazon_base_url : str
        Base URL for Amazon search.
    blinkit_base_url : str
        Base URL for Blinkit search.
    amazon_affiliate_code : str
        Amazon affiliate code to be appended to the search URL.

    Methods
    -------
    generate_amazon_link(ingredient: str) -> str
        Generates an Amazon search link for the given ingredient with affiliate code.
    generate_blinkit_link(ingredient: str) -> str
        Generates a Blinkit search link for the given ingredient.
    get_links(ingredients: list) -> dict
        Generates a dictionary of shopping links for a list of ingredients.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the ShoppingLinkGenerator object.

        Parameters
        ----------
        amazon_affiliate_code : str
            Amazon affiliate code to be appended to the search URL.
        """
        self.amazon_base_url = "https://www.amazon.in/s"
        self.blinkit_base_url = "https://blinkit.com/s/"
        self.amazon_affiliate_code = os.getenv('affiliate_code')  # Amazon affiliate code

    def generate_amazon_link(self, ingredient: str) -> str:
        """
        Generates an Amazon search link for the given ingredient with affiliate code.

        Parameters
        ----------
        ingredient : str
            The ingredient to search for on Amazon.

        Returns
        -------
        str
            The generated Amazon search link with affiliate code.
        """
        query_params = {
            'k': ingredient,
            'linkCode': 'll2',
            'tag': self.amazon_affiliate_code
        }
        return f"{self.amazon_base_url}?{urllib.parse.urlencode(query_params)}"

    def generate_blinkit_link(self, ingredient: str) -> str:
        """
        Generates a Blinkit search link for the given ingredient.

        Parameters
        ----------
        ingredient : str
            The ingredient to search for on Blinkit.

        Returns
        -------
        str
            The generated Blinkit search link.
        """
        query_params = {'q': ingredient}
        return f"{self.blinkit_base_url}?{urllib.parse.urlencode(query_params)}"

    def get_links(self, ingredients: list) -> dict:
        """
        Generates a dictionary of shopping links for a list of ingredients.

        Parameters
        ----------
        ingredients : list
            A list of ingredients to generate shopping links for.

        Returns
        -------
        dict
            A dictionary where each key is an ingredient and the value is another dictionary
            containing the Amazon and Blinkit links.
        """
        links = {}
        for ingredient in ingredients:
            links[ingredient] = {
                'Amazon': self.generate_amazon_link(ingredient),
                'Blinkit': self.generate_blinkit_link(ingredient)
            }
        return links
