from PyQt4.QtGui import QMessageBox
min_boundary = 0.01  # m^2
med_boundary = 10  # m^2

min_features = {}
med_features = {}
max_features = {}
layer = qgis.utils.iface.activeLayer()

for feat in layer.getFeatures():
    fid = feat.id()
    geom = feat.geometry()
    area = geom.area()

    if area < min_boundary:
        min_features[fid] = area
    elif area >= min_boundary and area < med_boundary:
        med_features[fid] = area
    else:
        max_features[fid] = area

def delete_features(layer, features, text):
    ids = features.keys()
    if len(ids) == 0:
        return
    question = ('Do you want to delete all the following features with area %s' % text)

    features_text = 'FID: area\n'
    for fid, area in features.iteritems():
        features_text += '%s: %s\n' % (fid, area)

    mb = QMessageBox(
        QMessageBox.Question,
        'Confirm deletion',
        question,
        QMessageBox.Yes | QMessageBox.No)
    mb.setDetailedText(features_text)
    # mb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    mb.setSizeGripEnabled(True)

    if mb.exec_() == QMessageBox.Yes:
        layer.startEditing()
        layer.dataProvider().deleteFeatures( ids )
        layer.commitChanges()

text = 'under %s' % min_boundary
delete_features(layer, min_features, text)

text = 'between %s and %s' % (min_boundary, med_boundary)
delete_features(layer, med_features, text)

# text = 'over %s' % med_boundary
# delete_features(layer, max_features, text)

# print 'Features with area over %s' % med_boundary
# print max_features.keys()
