
from share2.shareCore.views import ViewCore
from share2.shareCore.models import Feature
from share2.shareGeocam.search import SearchGeocam

class ViewGeocam(ViewCore):
    def getMatchingFeaturesForQuery(self, query):
        features = Feature.objects.all()
        if query:
            features = SearchGeocam().searchFeatures(features, query)
        return features

viewSingleton = ViewGeocam()