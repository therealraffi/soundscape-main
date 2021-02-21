import SwiftUI

struct Sound: Codable {
    let classification: String
    let content: String
    let speaking: String
}

struct ContentView: View {
    @State private var sound = [String: Sound]()

    @State private var sound1 = "";
    @State private var sound2 = "";
    @State private var sound3 = "";
    @State private var sound4 = "";
    
    @State private var speaking1 = "";
    @State private var speaking2 = "";
    @State private var speaking3 = "";
    @State private var speaking4 = "";
    
    let timer = Timer.publish(every: 0.5, on: .current, in: .common).autoconnect()
    
    @State private var colors_classify = [
        //Green to blue
        Color(red: 6/255, green: 214/255, blue: 160/255),
        Color(red: 10/255, green: 133/255, blue: 237/255)
    ]
    
    @State private var colors_speech = [
        //Blue to purple
        Color(red: 40/255, green: 63/255, blue: 237/255),
        Color(red: 110/255, green: 68/255, blue: 255/255)
    ]
    
    var body: some View {
        ScrollView {
            VStack (spacing: 9) {
                /*List {
                    for (key,value) in self.sound {
                        Text(key)
                    }
                }*/
                Text(sound1).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: self.backColor(self.speaking1)), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.fontSize(self.sound1)))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                
                Text(sound2).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: self.backColor(self.speaking2)), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.fontSize(self.sound2)))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                
                Text(sound3).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: self.backColor(self.speaking3)), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.fontSize(self.sound3)))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                
                Text(sound4).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: self.backColor(self.speaking4)), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.fontSize(self.sound4)))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                
            }.frame(maxWidth: .infinity).onAppear(perform: loadData).onReceive(timer) { _ in
                self.loadData()
                //print(self.sound)
                
                //for (key,value) in self.sound {
               //     print(key, value, value.classification)
                //}
                //print(self.s1, self.s1[0])
                //ForEach(self.sound.keys.sorted()) { result in
                //    print(result)
                //}
            }
        }
    }
}

extension ContentView {
    func backColor(_ str: String) -> [Color] {
        if str == "true" {
            return self.colors_speech
        }
        return self.colors_classify
    }
    
    func fontSize(_ str : String) -> Int {
        if str.count > 18 {
            return 14
        }
        if str.count > 12 {
            return 16
        }
        return 18
    }
    
    func loadData() {
        guard let url = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound.json") else {
            return
        }
        
        let request = URLRequest(url: url)
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode([String: Sound].self, from: data) {
                    DispatchQueue.main.async {
                        self.sound = decodedData

                        self.sound1 = String(decodedData["sound1"]?.classification ?? "")
                        self.speaking1 = String(decodedData["sound1"]?.speaking ?? "")
                        self.sound2 = String(decodedData["sound2"]?.classification ?? "")
                        self.speaking2 = String(decodedData["sound2"]?.speaking ?? "")
                        self.sound3 = String(decodedData["sound3"]?.classification ?? "")
                        self.speaking3 = String(decodedData["sound3"]?.speaking ?? "")
                        self.sound4 = String(decodedData["sound4"]?.classification ?? "")
                        self.speaking4 = String(decodedData["sound4"]?.speaking ?? "")
                    }
                }
            }
        }.resume()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

