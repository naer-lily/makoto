package com.makoto.android.ui.profile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.makoto.android.data.remote.dto.ProfileResponse
import com.makoto.android.data.repository.ProfileRepository
import com.makoto.android.ui.components.MakotoScaffold

@Composable
fun ProfileScreen(
    profileRepo: ProfileRepository,
    navController: NavController,
    viewModel: ProfileViewModel = viewModel(
        factory = ProfileViewModelFactory(profileRepo),
    ),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    MakotoScaffold(title = "个人画像", navController = navController) { padding ->
        if (state.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }
        } else if (state.error != null) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(state.error!!, color = MaterialTheme.colorScheme.error)
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(onClick = viewModel::load) { Text("重试") }
                }
            }
        } else {
            state.profile?.let { profile ->
                ProfileContent(profile, modifier = Modifier.padding(padding))
            }
        }
    }
}

@Composable
private fun ProfileContent(profile: ProfileResponse, modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(profile.name, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "${genderLabel(profile.gender)}  ·  ${profile.age}岁  ·  ${profile.heightCm.toInt()}cm",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }

        item { SectionTitle("身体指标") }
        item {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ProfileStat("体重", "${String.format("%.1f", profile.weightKg)} kg", Modifier.weight(1f))
                ProfileStat("体脂率", "${String.format("%.1f", profile.bodyFatPct)}%", Modifier.weight(1f))
                ProfileStat("去脂体重", "${String.format("%.1f", profile.ffmKg)} kg", Modifier.weight(1f))
            }
        }

        item { SectionTitle("目标") }
        item {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ProfileStat("目标体重", "${String.format("%.1f", profile.targetWeightKg)} kg", Modifier.weight(1f))
                ProfileStat("目标日期", profile.targetDate, Modifier.weight(1f))
                ProfileStat("剩余天数", "${profile.daysRemaining}天", Modifier.weight(1f))
            }
        }

        item { SectionTitle("能量消耗") }
        item {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ProfileStat("BMR", "${profile.bmrKcal.toInt()} kcal", Modifier.weight(1f))
                ProfileStat("TDEE", "${profile.neteeKcal.toInt()} kcal", Modifier.weight(1f))
                profile.weeklyDeficitNeeded?.let {
                    ProfileStat("周缺口", "${it.toInt()} kcal", Modifier.weight(1f))
                }
            }
        }

        item { SectionTitle("活动水平") }
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(
                    activityLabel(profile.activityLevel),
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }

        item { Spacer(modifier = Modifier.height(8.dp)) }
    }
}

@Composable
private fun SectionTitle(title: String) {
    Text(
        title,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.padding(vertical = 4.dp),
    )
}

@Composable
private fun ProfileStat(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier = modifier, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(modifier = Modifier.padding(10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun genderLabel(gender: String): String = when (gender) {
    "male" -> "男"
    "female" -> "女"
    else -> gender
}

private fun activityLabel(level: String): String = when (level) {
    "sedentary" -> "久坐不动"
    "light" -> "轻度活动"
    "moderate" -> "中度活动"
    "active" -> "积极运动"
    "very_active" -> "高强度运动"
    else -> level
}

internal class ProfileViewModelFactory(
    private val profileRepo: ProfileRepository,
) : androidx.lifecycle.ViewModelProvider.Factory {
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return ProfileViewModel(profileRepo) as T
    }
}
