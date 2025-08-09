**Proje Adı**: SUMO Simülasyon Verileri ve Makine Öğrenmesi ile Elektrikli Araç Enerji Tüketimi Tahmini

**Koordinatör**: Ahmet Alperen Polat

**E-mail**: alperenahmetpolat@gmail.com

**Proje Kısa Amacı/Tanımı:** Bu projenin temel amacı, SUMO (Simulation of Urban MObility) trafik simülatörü kullanılarak oluşturulan elektrikli araç sürüş senaryolarından elde edilen verilerle bir enerji tüketim tahmin modeli geliştirmektir. Katılımcılar, SUMO'da çeşitli yol ve trafik koşullarını içeren sürüş döngüleri (trip) oluşturacak, bu simülasyonlardan elde ettikleri verilerle (hız, ivme, araç ağırlığı,  yol eğimi[default olarak bulunmamaktadır] vb.) detaylı bir veri seti hazırlayacaktır. Veri seti hazırlık aşamasında gruplar birlikte çalışacak ardından hazırladıkları veri setini koordinatörün onayına sunacaklardır. Sonrasında her grup ayrı olmak üzere, bu veri setini kullanarak biri yapay sinir ağı olmak üzere en az üç farklı makine öğrenmesi algoritmasını eğitecek, modellerin tahmin performanslarını karşılaştıracak ve en başarılı modelin sonuçlarını teknik gerekçeleriyle birlikte sunacaklardır.

Kaynaklar:

- [**https://sumo.dlr.de/docs/index.html**](https://sumo.dlr.de/docs/index.html)
- [**https://sumo.dlr.de/docs/TraCI.html**](https://sumo.dlr.de/docs/TraCI.html)
- [**https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html**](https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html)
- [**https://developers.google.com/maps/documentation/elevation/start**](https://developers.google.com/maps/documentation/elevation/start)
- [**SUMO User Conf. YT**](https://youtube.com/playlist?list=PLy7t4z5SYNaQCvbv4IVIbPBEtRDNm0uxq&si=TYnprjVlL6qJZbQY)
- [**Scikit Learn**](https://scikit-learn.org/0.21/documentation.html)
- [**PyTorch**](https://docs.pytorch.org/docs/stable/index.html)

**Proje Gereksinimleri**:

- **G1:** SUMO trafik simülasyon ortamının kurulması ve temel seviyede kullanılabilmesi.
- **G2:** SUMO üzerinde belirlenecek senaryolara uygun olarak elektrikli araç rotalarının ve sürüş profillerinin oluşturulması.
- **G3:** Simülasyonlar sonucunda araçların anlık hız, ivme, konum ve yol eğimi gibi enerji tüketimini etkileyen verilerin çekilmesi.
- **G4:** Çekilen ham verilerin temizlenerek, işlenerek ve birleştirilerek yapısal bir makine öğrenmesi veri setinin oluşturulması.
- **G5:** Oluşturulan veri seti kullanılarak, biri özel olarak tasarlanmış bir yapay sinir ağı (neural network) olmak üzere en az üç farklı makine öğrenmesi modeli ile enerji tüketimi tahmini yapılması.
- **G6:** Yapay sinir ağı modelinin katman ve nöron sayısı, aktivasyon fonksiyonları gibi hiperparametrelerinin basit bir yapıdan kaçınılarak, gerekçelendirilerek tasarlanması.
- **G7:** Modellerin performans metrikleri (örneğin, MAE, RMSE) üzerinden karşılaştırılması, en iyi sonuç veren modelin başarısının altında yatan nedenlerin teknik olarak açıklanması ve sonuçların bir sunum ile raporlanması.