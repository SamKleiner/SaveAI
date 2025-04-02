//
//  SettingsView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

// Settings and Store Status
struct SettingsView: View {
    @StateObject private var storeStatusViewModel = StoreStatusViewModel()
    @State private var vacancyRateInput: String = ""
    @State private var lineLengthInput: String = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Store Status")) {
                    TextField("Vacancy Rate (%)", text: $vacancyRateInput)
                        .keyboardType(.decimalPad)
                    TextField("Line Length", text: $lineLengthInput)
                        .keyboardType(.numberPad)
                    Button("Update Store Status") {
                        if let vacancy = Double(vacancyRateInput),
                           let line = Int(lineLengthInput) {
                            storeStatusViewModel.vacancyRate = vacancy
                            storeStatusViewModel.lineLength = line
                            storeStatusViewModel.updateStoreStatus()
                        }
                    }
                }
                Section(header: Text("Additional Settings")) {
                    NavigationLink("Manage Profit Groups", destination: ProfitGroupManagementView())
                }
            }
            .navigationTitle("Settings")
        }
    }
}
