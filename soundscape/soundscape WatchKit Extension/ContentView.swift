import SwiftUI

struct Sound: Codable {
    let classification: String
    let content: String
    let speaking: String
}

struct ContentView: View {
    @State private var sound = [String: Sound]()
    
    let timer = Timer.publish(every: 0.25, on: .current, in: .common).autoconnect()
    
    @State private var colors_classify = [
        //Green to blue
        Color(red: 6/255, green: 214/255, blue: 160/255),
        Color(red: 6/255, green: 214/255, blue: 160/255)
    ]
    
    @State private var colors_speech = [
        //Blue to purple
        Color(red: 59/255, green: 181/255, blue: 252/255),
        Color(red: 59/255, green: 181/255, blue: 252/255)
    ]

    var body: some View {
        ScrollView {
            VStack (spacing: 7) {
                if self.sound["sound1"] != nil {
                    self.text(self.sound["sound1"]!)
                    self.text(self.sound["sound2"]!)
                    self.text(self.sound["sound3"]!)
                    self.text(self.sound["sound4"]!)
                }
            }.frame(maxWidth: .infinity).onAppear(perform: loadData).onReceive(timer) { _ in
                self.loadData()
            }
        }
    }
}

extension ContentView {
    func fontSize(_ str : String) -> Int {
        if str.count > 12 {
            return 15
        }
        if str.count > 18 {
            return 14
        }
        return 16
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
                    }
                }
            }
        }.resume()
    }
    
    func text(_ Case: Sound) -> some View {
        let text = Case.speaking == "true" ? Case.content : Case.classification
        let color = Case.speaking == "true" ? self.colors_speech : self.colors_classify
        return Text(text).padding(EdgeInsets(top: 4, leading: 12, bottom: 4, trailing: 12)).background(LinearGradient(gradient: Gradient(colors: color), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(fontSize(text)))).lineLimit(nil).animation(.easeInOut(duration:0.5))
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
