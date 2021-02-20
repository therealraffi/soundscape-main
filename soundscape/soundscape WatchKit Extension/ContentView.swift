import SwiftUI

struct Sound: Codable {
    let classification: String
    let content: String
    let speaking: String
}

struct ContentView: View {
    @State private var sound1 = "";
    @State private var sound2 = "";
    @State private var sound3 = "";
    @State private var sound4 = "";
    
    @State private var f1 = 18;
    @State private var f2 = 18;
    @State private var f3 = 18;
    @State private var f4 = 18;
    
    let timer = Timer.publish(every: 0.5, on: .current, in: .common).autoconnect()
    
    private let colors = [
        Color(red: 6/255, green: 214/255, blue: 160/255),
        Color(red: 10/255, green: 133/255, blue: 237/255)
    ]
    
    var body: some View {
        ZStack {
            ScrollView {
                VStack (spacing: 9) {
                    Text(sound1).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: colors), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.f1))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                    
                    Text(sound2).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: colors), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.f2))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                    
                    Text(sound3).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: colors), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.f3))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                    
                    Text(sound4).padding(EdgeInsets(top: 5, leading: 15, bottom: 5, trailing: 15)).background(LinearGradient(gradient: Gradient(colors: colors), startPoint: .top, endPoint: .bottom).edgesIgnoringSafeArea(.all)).cornerRadius(10).font(.system(size: CGFloat(self.f4))).lineLimit(nil).animation(.easeInOut(duration:0.5))
                   
                }.frame(maxWidth: .infinity).onAppear(perform: loadData).onReceive(timer) { _ in
                    self.loadData()
                    self.f1 = self.fontSize(str: self.sound1)
                    self.f2 = self.fontSize(str: self.sound2)
                    self.f3 = self.fontSize(str: self.sound3)
                    self.f4 = self.fontSize(str: self.sound4)
                }
            }
        }
    }
}

extension ContentView {
    func fontSize(str : String) -> Int {
        if str.count > 18 {
            return 14
        }
        if str.count > 12 {
            return 16
        }
        return 18
    }
    
    func loadData() {
        guard let url1 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound1.json") else {
            return
        }
        
        let request1 = URLRequest(url: url1)
        URLSession.shared.dataTask(with: request1) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound1 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url2 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound2.json") else {
            return
        }
        
        let request2 = URLRequest(url: url2)
        URLSession.shared.dataTask(with: request2) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound2 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url3 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound3.json") else {
            return
        }
        
        let request3 = URLRequest(url: url3)
        URLSession.shared.dataTask(with: request3) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound3 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url4 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound4.json") else {
            return
        }
        
        let request4 = URLRequest(url: url4)
        URLSession.shared.dataTask(with: request4) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound4 = decodedData.classification
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

